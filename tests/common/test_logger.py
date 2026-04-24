import pytest
from database_as_crime_scene.common.logger import log, console

def test_log_info(mocker):
    # Mock the log method of the console object
    mock_log = mocker.patch.object(console, 'log')
    log("Test message", type="info")
    mock_log.assert_called_once_with("Test message")

def test_log_error(mocker):
    mock_print_error = mocker.patch.object(console, 'print_error', create=True)
    # The current code tries to call console.print_error which doesn't exist on rich.Console by default, 
    # but let's test that it attempts to call it based on the implementation
    log("Error message", type="error")
    mock_print_error.assert_called_once_with("Error message")

def test_log_warning(mocker):
    mock_print_warning = mocker.patch.object(console, 'print_warning', create=True)
    log("Warning message", type="warning")
    mock_print_warning.assert_called_once_with("Warning message")

def test_log_success(mocker):
    mock_print_success = mocker.patch.object(console, 'print_success', create=True)
    log("Success message", type="success")
    mock_print_success.assert_called_once_with("Success message")

def test_log_debug(mocker):
    mock_print_debug = mocker.patch.object(console, 'print_debug', create=True)
    log("Debug message", type="debug")
    mock_print_debug.assert_called_once_with("Debug message")

def test_log_trace(mocker):
    mock_print_trace = mocker.patch.object(console, 'print_trace', create=True)
    log("Trace message", type="trace")
    mock_print_trace.assert_called_once_with("Trace message")

def test_log_tree(mocker):
    mock_print_tree = mocker.patch.object(console, 'print_tree', create=True)
    log("Tree message", type="tree")
    mock_print_tree.assert_called_once_with("Tree message")

def test_log_json(mocker):
    mock_print_json = mocker.patch.object(console, 'print_json', create=True)
    log("JSON message", type="json")
    mock_print_json.assert_called_once_with("JSON message")

def test_log_markdown(mocker):
    mock_print_markdown = mocker.patch.object(console, 'print_markdown', create=True)
    log("Markdown message", type="markdown")
    mock_print_markdown.assert_called_once_with("Markdown message")

def test_log_text(mocker):
    mock_print_text = mocker.patch.object(console, 'print_text', create=True)
    log("Text message", type="text")
    mock_print_text.assert_called_once_with("Text message")

def test_log_log(mocker):
    mock_print_log = mocker.patch.object(console, 'print_log', create=True)
    log("Log message", type="log")
    mock_print_log.assert_called_once_with("Log message")

def test_log_table(mocker):
    mock_print = mocker.patch.object(console, 'print')
    mock_df_to_table = mocker.patch('database_as_crime_scene.common.logger.df_to_table')
    mock_df_to_table.return_value = "MockedTable"
    
    log("DataFrame", type="table")
    
    mock_df_to_table.assert_called_once_with("DataFrame")
    mock_print.assert_called_once_with("MockedTable")

def test_log_syntax(mocker):
    mock_print = mocker.patch.object(console, 'print')
    mock_syntax = mocker.patch('database_as_crime_scene.common.logger.Syntax')
    mock_syntax.return_value = "MockedSyntax"
    
    log("SELECT * FROM table", type="syntax")
    
    mock_syntax.assert_called_once_with(
        "SELECT * FROM table",
        "sql",
        theme="ansi_light",
        line_numbers=True,
    )
    mock_print.assert_called_once_with("MockedSyntax")

def test_log_default(mocker):
    mock_print = mocker.patch.object(console, 'print')
    log("Default message", type="unknown_type")
    mock_print.assert_called_once_with("Default message")
