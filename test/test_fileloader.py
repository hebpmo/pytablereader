# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import print_function, unicode_literals

from textwrap import dedent

import pathvalidate as pv
import pytablereader as ptr
import pytest
import six
from mbstrdecoder import MultiByteStrDecoder
from path import Path
from pytablereader.interface import TableLoader
from pytablewriter import ExcelXlsxTableWriter, dump_tabledata
from tabledata import TableData


class Test_TableFileLoader_get_format_name_list(object):
    def test_normal(self):
        format_name_list = ptr.TableFileLoader.get_format_name_list()

        assert format_name_list == [
            "csv",
            "excel",
            "html",
            "json",
            "json_lines",
            "jsonl",
            "ldjson",
            "ltsv",
            "markdown",
            "mediawiki",
            "ndjson",
            "sqlite",
            "ssv",
            "tsv",
        ]


class Test_TableFileLoader_constructor(object):
    @pytest.mark.parametrize(
        ["file_path", "format_name", "expected"],
        [
            ["/tmp/valid/test/data/validext.csv", None, ptr.CsvTableFileLoader],
            [
                "/tmp/valid/test/新しいフォルダー/新しいテキスト ドキュメント.csv".encode("utf_8"),
                None,
                ptr.CsvTableFileLoader,
            ],
            ["/tmp/validext.xlsx", None, ptr.ExcelTableFileLoader],
            ["/tmp/validext.html", None, ptr.HtmlTableFileLoader],
            ["/tmp/validext.json", None, ptr.JsonTableFileLoader],
            ["/tmp/validext.jsonl", None, ptr.JsonLinesTableFileLoader],
            ["/tmp/validext.ldjson", None, ptr.JsonLinesTableFileLoader],
            ["/tmp/validext.ltsv", None, ptr.LtsvTableFileLoader],
            ["/tmp/validext.md", None, ptr.MarkdownTableFileLoader],
            ["/tmp/validext.ndjson", None, ptr.JsonLinesTableFileLoader],
            ["/tmp/validext.tsv", None, ptr.TsvTableFileLoader],
            ["/tmp/validext.txt", "csv", ptr.CsvTableFileLoader],
            ["/tmp/テスト.txt".encode("utf_8"), "csv", ptr.CsvTableFileLoader],
            ["/tmp/validext.txt", "ssv", ptr.CsvTableFileLoader],
            ["/tmp/validext.txt", "html", ptr.HtmlTableFileLoader],
            ["/tmp/validext.txt", "json", ptr.JsonTableFileLoader],
            ["/tmp/validext.txt", "jsonl", ptr.JsonLinesTableFileLoader],
            ["/tmp/validext.txt", "json_lines", ptr.JsonLinesTableFileLoader],
            ["/tmp/validext.txt", "ldjson", ptr.JsonLinesTableFileLoader],
            ["/tmp/invalidext.txt", "markdown", ptr.MarkdownTableFileLoader],
            ["/tmp/invalidext.txt", "mediawiki", ptr.MediaWikiTableFileLoader],
            ["/tmp/validext.txt", "ndjson", ptr.JsonLinesTableFileLoader],
        ],
    )
    def test_normal(self, tmpdir, file_path, format_name, expected):
        test_file_path = Path(
            six.text_type(tmpdir.join(Path(MultiByteStrDecoder(file_path).unicode_str)))
        )
        test_file_path.parent.makedirs_p()

        with open(test_file_path, "w") as f:
            f.write("""{}""")

        loader = ptr.TableFileLoader(test_file_path, format_name=format_name)
        expected_loader = expected("")

        assert loader.source_type == expected_loader.source_type
        assert loader.format_name == expected_loader.format_name

    @pytest.mark.parametrize(
        ["value", "format_name", "expected"],
        [
            [None, None, ValueError],
            ["", None, ptr.InvalidFilePathError],
            ["https://github.com/", None, ptr.LoaderNotFoundError],
            ["/tmp/test.txt", None, ptr.LoaderNotFoundError],
            ["c:\\tmp\test.txt", None, ptr.LoaderNotFoundError],
            ["/tmp/valid/test/data/validext.csv/", None, ptr.LoaderNotFoundError],
            ["/tmp/invalid/test/data/invalidext.txt", "invalidformat", ptr.LoaderNotFoundError],
        ],
    )
    def test_exception(self, value, format_name, expected):
        with pytest.raises(expected):
            ptr.TableFileLoader(value, format_name=format_name)


class Test_TableFileLoader_load(object):
    def setup_method(self, method):
        TableLoader.clear_table_count()

    @pytest.mark.parametrize(
        ["file_path", "format_name"],
        [
            ["/tmp/valid/test/data/validdata.csv", None],
            ["/tmp/valid/test/data/validdata.txt", "csv"],
        ],
    )
    def test_normal_csv(self, tmpdir, file_path, format_name):
        filename = pv.replace_symbol(file_path, "")
        p_file_path = Path(six.text_type(tmpdir.join(filename + Path(file_path).ext)))
        p_file_path.parent.makedirs_p()

        with open(p_file_path, "w") as f:
            f.write(
                dedent(
                    """\
                "attr_a","attr_b","attr_c"
                1,4,"a"
                2,2.1,"bb"
                3,120.9,"ccc"
                """
                )
            )

        expeced_list = [
            TableData(
                filename,
                ["attr_a", "attr_b", "attr_c"],
                [[1, 4, "a"], [2, "2.1", "bb"], [3, "120.9", "ccc"]],
            )
        ]
        loader = ptr.TableFileLoader(p_file_path, format_name=format_name)

        assert loader.format_name == "csv"

        for tabledata, expected in zip(loader.load(), expeced_list):
            print(dump_tabledata(expected))
            print(dump_tabledata(tabledata))

            assert tabledata.equals(expected)

    def test_normal_ssv(self, tmpdir):
        p_file_path = Path(six.text_type(tmpdir.join("testdata.txt")))
        p_file_path.parent.makedirs_p()

        with open(p_file_path, "w") as f:
            f.write(
                dedent(
                    """\
                USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
                root         1  0.0  0.4  77664  8784 ?        Ss   May11   0:02 /sbin/init
                root         2  0.0  0.0      0     0 ?        S    May11   0:00 [kthreadd]
                root         4  0.0  0.0      0     0 ?        I<   May11   0:00 [kworker/0:0H]
                root         6  0.0  0.0      0     0 ?        I<   May11   0:00 [mm_percpu_wq]
                root         7  0.0  0.0      0     0 ?        S    May11   0:01 [ksoftirqd/0]
                """
                )
            )

        expeced_list = [
            TableData(
                "testdata",
                [
                    "USER",
                    "PID",
                    "%CPU",
                    "%MEM",
                    "VSZ",
                    "RSS",
                    "TTY",
                    "STAT",
                    "START",
                    "TIME",
                    "COMMAND",
                ],
                [
                    ["root", 1, 0, 0.4, 77664, 8784, "?", "Ss", "May11", "0:02", "/sbin/init"],
                    ["root", 2, 0, 0, 0, 0, "?", "S", "May11", "0:00", "[kthreadd]"],
                    ["root", 4, 0, 0, 0, 0, "?", "I<", "May11", "0:00", "[kworker/0:0H]"],
                    ["root", 6, 0, 0, 0, 0, "?", "I<", "May11", "0:00", "[mm_percpu_wq]"],
                    ["root", 7, 0, 0, 0, 0, "?", "S", "May11", "0:01", "[ksoftirqd/0]"],
                ],
            )
        ]
        loader = ptr.TableFileLoader(p_file_path, format_name="ssv")

        assert loader.format_name == "csv"

        for tabledata, expected in zip(loader.load(), expeced_list):
            print(dump_tabledata(expected))
            print(dump_tabledata(tabledata))

            assert tabledata.equals(expected)

    @pytest.mark.parametrize(
        ["file_path", "format_name"],
        [
            ["/tmp/valid/test/data/validdata.json", None],
            ["/tmp/valid/test/data/validdata.txt", "json"],
        ],
    )
    def test_normal_json(self, tmpdir, file_path, format_name):
        p_file_path = Path(str(tmpdir.join(file_path)))
        p_file_path.parent.makedirs_p()

        with open(p_file_path, "w") as f:
            f.write(
                dedent(
                    """\
                [
                    {"attr_a": 1},
                    {"attr_b": 2.1, "attr_c": "bb"}
                ]"""
                )
            )

        expeced_list = [
            TableData(
                "validdata",
                ["attr_a", "attr_b", "attr_c"],
                [{"attr_a": 1}, {"attr_b": 2.1, "attr_c": "bb"}],
            )
        ]
        loader = ptr.TableFileLoader(p_file_path, format_name=format_name)

        assert loader.format_name == "json"

        for table_data, expected in zip(loader.load(), expeced_list):
            assert table_data.equals(expected)

    @pytest.mark.xfail(run=False)
    def test_normal_excel(self, tmpdir):
        file_path = "/tmp/valid/test/data/validdata.xlsx"
        p_file_path = Path(str(tmpdir.join(file_path)))
        p_file_path.parent.makedirs_p()

        tabledata_list = [
            TableData(
                table_name="testsheet1",
                header_list=["a1", "b1", "c1"],
                row_list=[
                    ["aa1", "ab1", "ac1"],
                    [1.0, 1.1, "a"],
                    [2.0, 2.2, "bb"],
                    [3.0, 3.3, 'cc"dd"'],
                ],
            ),
            TableData(
                table_name="testsheet3",
                header_list=["a3", "b3", "c3"],
                row_list=[["aa3", "ab3", "ac3"], [4.0, 1.1, "a"], [5.0, "", "bb"], [6.0, 3.3, ""]],
            ),
        ]

        writer = ExcelXlsxTableWriter()
        writer.open(p_file_path)
        for tabledata in tabledata_list:
            writer.from_tabledata(tabledata)
        writer.write_table()
        writer.close()

        loader = ptr.TableFileLoader(p_file_path)

        assert loader.format_name == "excel"

        for tabledata in loader.load():
            print(dump_tabledata(tabledata))

            assert tabledata in tabledata_list
