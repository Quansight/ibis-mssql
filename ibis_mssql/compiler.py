import pyodbc
import sqlalchemy as sa
import sqlalchemy.dialects.mssql as mssql

import ibis.common.exceptions as com
import ibis.expr.datatypes as dt
import ibis.expr.operations as ops
import ibis.sql.alchemy as alch

# used for literal translate
from ibis.sql.alchemy import fixed_arity, unary


def raise_unsupported_op_error(translator, expr, *args):
    msg = "SQLServer backend doesn't support {} operation!"
    op = expr.op()
    raise com.UnsupportedOperationError(msg.format(type(op)))


# Aggregation
# coppied from postgresql compiler
# support for of bit columns in aggregate methods
def _reduction(func_name, cast_type='int32'):
    def reduction_compiler(t, expr):
        arg, where = expr.op().args

        if arg.type().equals(dt.boolean):
            arg = arg.cast(cast_type)

        func = getattr(sa.func, func_name)

        if where is not None:
            arg = where.ifelse(arg, None)
        return func(t.translate(arg))

    return reduction_compiler


# String
# TODO: substr and find are copied from SQLite, we should really have a
# "base" set of SQL functions that are the most common APIs across the major
# RDBMS
def _substr(t, expr):
    f = sa.func.substring

    arg, start, length = expr.op().args

    sa_arg = t.translate(arg)
    sa_start = t.translate(start)

    if length is None:
        return f(sa_arg, sa_start + 1)
    else:
        sa_length = t.translate(length)
        return f(sa_arg, sa_start + 1, sa_length)


def _string_find(t, expr):
    arg, substr, start, _ = expr.op().args

    sa_arg = t.translate(arg)
    sa_substr = t.translate(substr)

    if start is not None:
        sa_start = t.translate(start)
        return sa.func.charindex(sa_substr, sa_arg, sa_start) - 1

    return sa.func.charindex(sa_substr, sa_arg) - 1


# Numerical
def _floor_divide(t, expr):
    left, right = map(t.translate, expr.op().args)
    return sa.func.floor(left / right)


def _extract(fmt):
    def translator(t, expr):
        (arg,) = expr.op().args
        sa_arg = t.translate(arg)
        # sa.literal_column is used becuase it makes the argument pass
        # in NOT as a parameter
        return sa.cast(
            sa.func.datepart(sa.literal_column(fmt), sa_arg), sa.SMALLINT
        )

    return translator


_operation_registry = alch._operation_registry.copy()

_operation_registry.update(
    {
        # aggregate methods
        ops.Count: _reduction(sa.func.count),
        ops.Max: _reduction('max'),
        ops.Min: _reduction('min'),
        ops.Sum: _reduction('sum'),
        ops.Mean: _reduction('avg', 'float64'),
        # string methods
        ops.LStrip: unary(sa.func.ltrim),
        ops.Lowercase: unary(sa.func.lower),
        ops.RStrip: unary(sa.func.rtrim),
        ops.Repeat: fixed_arity(sa.func.replicate, 2),
        ops.Reverse: unary(sa.func.reverse),
        ops.StringFind: _string_find,
        ops.StringLength: unary(sa.func.length),
        ops.StringReplace: fixed_arity(sa.func.replace, 3),
        ops.Strip: unary(sa.func.trim),
        ops.Substring: _substr,
        ops.Uppercase: unary(sa.func.upper),
        # math
        ops.Abs: unary(sa.func.abs),
        ops.Acos: unary(sa.func.acos),
        ops.Asin: unary(sa.func.asin),
        ops.Atan2: fixed_arity(sa.func.atn2, 2),
        ops.Atan: unary(sa.func.atan),
        ops.Ceil: unary(sa.func.ceiling),
        ops.Cos: unary(sa.func.cos),
        ops.Floor: unary(sa.func.floor),
        ops.FloorDivide: _floor_divide,
        ops.Power: fixed_arity(sa.func.power, 2),
        ops.Sign: unary(sa.func.sign),
        ops.Sin: unary(sa.func.sin),
        ops.Sqrt: unary(sa.func.sqrt),
        ops.Tan: unary(sa.func.tan),
        # timestamp methods
        ops.TimestampNow: fixed_arity(sa.func.GETDATE, 0),
        ops.ExtractYear: _extract('year'),
        ops.ExtractMonth: _extract('month'),
        ops.ExtractDay: _extract('day'),
        ops.ExtractHour: _extract('hour'),
        ops.ExtractMinute: _extract('minute'),
        ops.ExtractSecond: _extract('second'),
        ops.ExtractMillisecond: _extract('millisecond'),
    }
)


_unsupported_ops = [
    # standard operations
    ops.NotContains,
    ops.NullIf,
    ops.NotAny,
    # miscellaneous
    ops.Least,
    ops.Greatest,
    # numeric
    ops.Round,
    ops.Log2,
    ops.Ln,
    ops.Log10,
    ops.Log,
    ops.Exp,
    ops.Modulus,
    # string
    ops.Contains,
    ops.LPad,
    ops.RPad,
    ops.Capitalize,
    ops.RegexSearch,
    ops.RegexExtract,
    ops.RegexReplace,
    ops.StringAscii,
    ops.StringSQLLike,
    # aggregate methods
    ops.CumulativeMax,
    ops.CumulativeMin,
    ops.CumulativeMean,
    ops.CumulativeSum,
    # datetime methods
    ops.TimestampTruncate,
]


_unsupported_ops = {k: raise_unsupported_op_error for k in _unsupported_ops}
_operation_registry.update(_unsupported_ops)


class MSSQLExprTranslator(alch.AlchemyExprTranslator):
    _registry = _operation_registry
    _rewrites = alch.AlchemyExprTranslator._rewrites.copy()
    _type_map = alch.AlchemyExprTranslator._type_map.copy()
    _type_map.update(
        {
            dt.Boolean: pyodbc.SQL_BIT,
            dt.Int8: mssql.TINYINT,
            dt.Int32: mssql.INTEGER,
            dt.Int64: mssql.BIGINT,
            dt.Float: mssql.REAL,
            dt.Double: mssql.REAL,
            dt.String: mssql.VARCHAR,
        }
    )


rewrites = MSSQLExprTranslator.rewrites
compiles = MSSQLExprTranslator.compiles


class MSSQLDialect(alch.AlchemyDialect):

    translator = MSSQLExprTranslator


dialect = MSSQLDialect
