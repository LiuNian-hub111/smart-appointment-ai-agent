from contextlib import contextmanager
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from ..models import Base


def migrate_teacher_schema(engine):
    """Preserve existing local bookings when upgrading the old domain names."""
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        renames = (("technicians", "teachers"), ("technician_schedules", "teacher_schedules"))
        for old_name, new_name in renames:
            if old_name in tables:
                if new_name in tables:
                    raise RuntimeError(f"Both {old_name} and {new_name} exist; migrate the database manually")
                connection.exec_driver_sql(f'ALTER TABLE "{old_name}" RENAME TO "{new_name}"')
                tables.remove(old_name)
                tables.add(new_name)

        for table in ("teacher_schedules", "user_behaviors", "user_recommendations"):
            if table in tables:
                columns = {column["name"] for column in inspect(connection).get_columns(table)}
                if "technician_id" in columns and "teacher_id" not in columns:
                    connection.exec_driver_sql(f'ALTER TABLE "{table}" RENAME COLUMN "technician_id" TO "teacher_id"')

        if "user_preferences" in tables:
            connection.exec_driver_sql(
                "UPDATE user_preferences SET preference_type = 'teacher' WHERE preference_type = 'technician'"
            )
        if "user_recommendations" in tables:
            connection.exec_driver_sql(
                "UPDATE user_recommendations SET recommendation_type = 'teacher_available' "
                "WHERE recommendation_type = 'technician_available'"
            )


class SessionManager:
    """
    数据库会话管理器

    职责：
    1. 管理数据库连接和会话
    2. 提供统一的会话上下文管理
    3. 处理事务和异常回滚
    """

    def __init__(self, db_path='sqlite:///data/smart_appointment.db'):
        """
        初始化会话管理器

        Args:
            db_path: 数据库连接路径
        """
        self.engine = create_engine(db_path)
        migrate_teacher_schema(self.engine)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    @contextmanager
    def session_scope(self):
        """
        提供会话上下文管理

        自动处理：
        - 会话创建和关闭
        - 事务提交和回滚
        - 异常处理
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def close(self):
        """关闭会话管理器"""
        self.Session.remove()
        self.engine.dispose()
