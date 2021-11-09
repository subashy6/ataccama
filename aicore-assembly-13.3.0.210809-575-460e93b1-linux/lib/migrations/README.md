# Cheatsheet for database migrations using Alembic and SQLAlchemy

DB schema should be usually created in one step by using DAO.define_tables() - not via DB schema migrations!
See the (Alembic cookbook)[https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-uptodate].
As the DB schema migrations have to parse individual version scripts to apply DDL operations, they are slower

While the migration scripts can theoretically do the same by migrating an empty database to head revision,
such capability serves ONLY for testing of DB schema migrations when a new revision is being added via
```
./manage.py schema drop
alembic upgrade head-1
alembic upgrade head
```

## Check the current DB schema revision

```
alembic current --verbose
```
Returns nothing if the database is not stamped by Alembic (which creates ```alembic_version``` table).

## Show available DB schema revisions

```
alembic history
```
Show the latest revision via ```alembic heads``` and details of a revision via ```alembic show <revision hash>```.

## Upgrade the DB schema

```
alembic upgrade head
```
Add ```--sql``` for a dry-run/preview of the migration (prints the SQL statements to stdout without executing them).
Beware, upgrade updates the current revision before running the script. If the upgrade script fails with an unhandled exception,
use ```alembic downgrade -1``` or ```alembic stamp <revision hash>``` before re-trying.

## Force-set a DB schema revision

```
alembic stamp <verison hash>
```

## Add new DB schema revision

```
alembic revision --autogenerate -m "C10"
```
Adjust the filename of newly created Python module in ```migrations/versions```  and its docstring as needed and implement at least the upgrade() function.
When deleting a revision created by mistake, jsut delete the module and update the hash in module for next revision (not needed when deleting head).
See the (Alembic tutorial)[https://alembic.sqlalchemy.org/en/latest/tutorial.html#create-a-migration-script].
See also the (documentation for Alembic operations)[https://alembic.sqlalchemy.org/en/latest/ops.html] for DDL manipulation commands.

```alembic.op.create_table()``` returns an instance of ```sqlalchmy.Table``` class which can be used the same way as in DAOs.
Existing classes should be mocked using sqlalchemy.table() with just the table name and subset of column names which we want to use (no constratints/data types/indexes).
Reflection of the current DB schema doesn't work in offline mode so the mock approach is strongly preferred.
Table definitions from DAO classes cannot be used since they describe the target state after migration.

## Cheatsheet for migration scripts

### Create table

```alembic.op.create_table()```

### Add column

```alembic.op.add_column()```
For columns with ```NOT NULL``` constraint: Temporarily disable the constraint via ```nullable=True``` before inserting values for the newly created column, then re-enable it.
See the HOWTO for (adding NOT NULL columns)[http://blog.simontaranto.com/post/2016-06-05-adding-a-boolean-column-to-an-existing-table-with-alembic-and-sqlalchemy]

### Drop table

```alembic.op.drop_table()```

### Query existing data

```alembic.op.execute(sqlalchemy.execute([some_table.c.column_name])).where(some_table.c.column_name == something)```

### Bulk-insert data

```alembic.op.bulk_insert(some_table, list_of_dicts)```
See the (Alembic docs for BULK INSERT)[http://alembic.zzzcomputing.com/en/latest/ops.html#alembic.operations.Operations.bulk_insert]

### Move data between tables

```alembic.op.execute(new_table.insert().from_select("column1", sqlalchemy.select(old_table.c.column1)))```
See the (Alembic docs for INSERT FROM SELECT)[http://docs.sqlalchemy.org/en/latest/core/dml.html#sqlalchemy.sql.expression.Insert.from_select]
and (Alembic docs for operations execute)[http://alembic.zzzcomputing.com/en/latest/ops.html#alembic.operations.Operations.execute]

### Insert literal values

```sqlalchemy.literal_column("'value'")```
And alias the column using ```sqlalchemy.label()``` to match the target column name.
See the (SQLAlchemy docs for literal columns)[http://docs.sqlalchemy.org/en/latest/core/sqlelement.html?highlight=case#sqlalchemy.sql.expression.literal_column]

### Update data based on another table

```
source_records = sqlalchemy.select(source_table.c.some_column).where(source_table.c.some_column == destination_table.c.some_column)
alembic.op.execute(destination_table.update().values(some_column=source_records))
```
Beware, ```update()``` doesn't support ```from_select()``` - see the (SQLAlchemy docs for correlated updates)[http://docs.sqlalchemy.org/en/rel_0_9/core/tutorial.html#correlated-updates] but CASE statement is supported -see (SQLAlchemy docs for CASE statement)[http://docs.sqlalchemy.org/en/latest/core/sqlelement.html?highlight=case#sqlalchemy.sql.expression.case].

### Delete data

```op.execute(destination_table.delete().where(destination_table.c.col1 == "val1"))```
See the (SQLAlchemy tutorial)[http://docs.sqlalchemy.org/en/rel_1_1/core/tutorial.html#deletes]

# Justification for DB-related changes

## Transforming all date-storing column types from DateTime to TIMESTAMP WITH TIMEZONE

Usage of dedicated `datetime` type instead of a simple `int` or `float` is attributed to the usage of the 
before-mentioned DB columns by two distinct components - AI-Core and MMM. To mitigate the potential issue of having to
synchronize the time between two components, the DB itself is chosen as the only source of time, ensuring time sync 
between the components.

Transforming the used column type from `DateTime` into `TIMESTAMP WITH TIMEZONE` is caused by any infrastructure 
component (like a DB server) being able to use different timezones. Thus, the application has to use the least common
denominator, which is UTC. To guarantee this, all of the `datetime` passed between components will be timezone-aware 
and contain an offset of `0` when queried from the DB.

