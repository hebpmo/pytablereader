# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <gogogo.vm@gmail.com>
"""

from __future__ import absolute_import
from __future__ import unicode_literals

import abc

import jsonschema
import six

from .._constant import TableNameTemplate as tnt
from ..error import ValidationError
from ..formatter import TableFormatter
from ..tabledata import TableData


class JsonConverter(TableFormatter):
    """
    The abstract class of JSON data converter.
    """

    _VALUE_TYPE_SCHEMA = {
        "anyOf": [
            {"type": "string"},
            {"type": "number"},
            {"type": "null"},
        ],
    }

    def __init__(self, json_buffer):
        self._buffer = json_buffer

    @abc.abstractproperty
    def _schema(self):  # pragma: no cover
        pass

    def _validate_source_data(self):
        """
        :raises ValidationError:
        """

        try:
            jsonschema.validate(self._buffer, self._schema)
        except jsonschema.ValidationError as e:
            raise ValidationError(e)


class SingleJsonTableConverterBase(JsonConverter):

    def _make_table_name(self):
        key = self._loader.get_format_key()

        return self._loader._replace_table_name_template(
            self._loader._get_basic_tablename_keyvalue_list() + [
                (tnt.KEY, key),
            ]
        )


class SingleJsonTableConverterA(SingleJsonTableConverterBase):
    """
    A concrete class of JSON table data formatter.
    """

    @property
    def _schema(self):
        return {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": self._VALUE_TYPE_SCHEMA,
            },
        }

    def to_table_data(self):
        """
        :raises ValueError:
        :raises pytablereader.error.ValidationError:
        """

        self._validate_source_data()

        attr_name_set = set()
        for json_record in self._buffer:
            attr_name_set = attr_name_set.union(six.viewkeys(json_record))

        self._loader.inc_table_count()

        yield TableData(
            table_name=self._make_table_name(),
            header_list=sorted(attr_name_set),
            record_list=self._buffer)


class SingleJsonTableConverterB(SingleJsonTableConverterBase):
    """
    A concrete class of JSON table data formatter.
    """

    @property
    def _schema(self):
        return {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": self._VALUE_TYPE_SCHEMA,
            },
        }

    def to_table_data(self):
        """
        :raises ValueError:
        :raises pytablereader.error.ValidationError:
        """

        self._validate_source_data()
        self._loader.inc_table_count()

        header_list = sorted(six.viewkeys(self._buffer))

        yield TableData(
            table_name=self._make_table_name(),
            header_list=header_list,
            record_list=zip(
                *[self._buffer.get(header) for header in header_list])
        )


class MultipleJsonTableConverterBase(JsonConverter):

    def __init__(self, json_buffer):
        super(MultipleJsonTableConverterBase, self).__init__(json_buffer)

        self._table_key = None

    def _make_table_name(self):
        return self._loader._replace_table_name_template(
            self._loader._get_basic_tablename_keyvalue_list() + [
                (tnt.KEY, self._table_key),
            ],
        )


class MultipleJsonTableConverterA(MultipleJsonTableConverterBase):
    """
    A concrete class of JSON table data converter.
    """

    @property
    def _schema(self):
        return {
            "type": "object",
            "additionalProperties": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": self._VALUE_TYPE_SCHEMA,
                },
            },
        }

    def to_table_data(self):
        """
        :raises ValueError:
        :raises pytablereader.error.ValidationError:
        """

        self._validate_source_data()

        for table_key, json_record_list in six.iteritems(self._buffer):
            attr_name_set = set()
            for json_record in json_record_list:
                attr_name_set = attr_name_set.union(six.viewkeys(json_record))

            self._loader.inc_table_count()
            self._table_key = table_key

            yield TableData(
                table_name=self._make_table_name(),
                header_list=sorted(attr_name_set),
                record_list=json_record_list)


class MultipleJsonTableConverterB(MultipleJsonTableConverterBase):
    """
    A concrete class of JSON table data converter.
    """

    @property
    def _schema(self):
        return {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": self._VALUE_TYPE_SCHEMA,
                },
            },
        }

    def to_table_data(self):
        """
        :raises ValueError:
        :raises pytablereader.error.ValidationError:
        """

        self._validate_source_data()

        for table_key, json_record_list in six.iteritems(self._buffer):
            header_list = sorted(six.viewkeys(json_record_list))

            self._loader.inc_table_count()
            self._table_key = table_key

            yield TableData(
                table_name=self._make_table_name(),
                header_list=header_list,
                record_list=zip(
                    *[json_record_list.get(header) for header in header_list])
            )


class JsonTableFormatter(TableFormatter):

    def to_table_data(self):
        converter_class_list = [
            MultipleJsonTableConverterA,
            MultipleJsonTableConverterB,
            SingleJsonTableConverterA,
            SingleJsonTableConverterB,
        ]

        for converter_class in converter_class_list:
            converter = converter_class(self._source_data)
            converter.accept(self._loader)
            try:
                for tabledata in converter.to_table_data():
                    yield tabledata
                return
            except ValidationError:
                pass
            else:
                break

        raise ValidationError(
            "inconvertible JSON schema: json={}".format(self._source_data))
