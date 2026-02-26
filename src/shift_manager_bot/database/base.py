from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# | Key | Type              | Index                   |
# | --- | ----------------- | ----------------------- |
# | ix  | Index             | ix_users_email          |
# | uq  | Unique constraint | uq_users_email          |
# | ck  | Check constraint  | ck_users_age_positive   |
# | fk  | Foreign key       | fk_orders_user_id_users |
# | pk  | Primary key       | pk_users                |

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
