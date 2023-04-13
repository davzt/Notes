import re
from datetime import datetime

from sqlalchemy import MetaData, DateTime
from sqlalchemy.orm import DeclarativeBase, declared_attr

convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata_obj = MetaData(naming_convention=convention)


def camel_to_snake(name):
    name = re.sub(r'((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))', r'_\1', name)
    return name.lower().lstrip('_')


class BaseORM(DeclarativeBase):
    __abstract__ = True

    metadata = metadata_obj

    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }

    @declared_attr
    def __tablename__(cls) -> str | None:
        return camel_to_snake(cls.__name__[:-3])

    # def __repr__(self):
    #     identity = inspect(self).identity
    #     pk = f'(transient {id(self)})' if identity is None else ', '.join(str(value) for value in identity)
    #     return f'<{self.__tablename__} {pk}>'
