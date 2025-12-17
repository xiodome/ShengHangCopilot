from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        # 避免在 migrate 时执行
        import sys
        if 'migrate' in sys.argv:
            return

        # 对于model.py中建表时无权限设置的default值，直接使用SQL语句进行设置
        from .views.initialTable import initialize_tables
        initialize_tables()
