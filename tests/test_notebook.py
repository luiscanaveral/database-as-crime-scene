import pytest
from database_as_crime_scene.notebook import Notebook, DatabaseAsCrimeScene

def test_notebook_sayHello(capsys):
    Notebook.sayHello()
    captured = capsys.readouterr()
    assert "Hello" in captured.out

def test_notebook_setup(mocker):
    # build_connection_string doesn't exist, we must mock it or it throws AttributeError
    mocker.patch.object(Notebook, 'build_connection_string', create=True)
    nb = Notebook()
    nb.setup()
    Notebook.build_connection_string.assert_called_once()

def test_notebook_print(mocker):
    mock_log = mocker.patch("database_as_crime_scene.notebook.log")
    Notebook.print("Test print")
    # args is passed as a tuple because of def print(*args):
    mock_log.assert_called_once_with(("Test print",))

def test_notebook_print_sql(mocker):
    mock_log = mocker.patch("database_as_crime_scene.notebook.log")
    Notebook.print_sql("SELECT *")
    mock_log.assert_called_once_with("SELECT *", type="syntax")

def test_database_as_crime_scene_singleton():
    db1 = DatabaseAsCrimeScene()
    db2 = DatabaseAsCrimeScene()
    
    assert db1 is db2
    assert db1.data == []

def test_database_as_crime_scene_setup(capsys):
    db = DatabaseAsCrimeScene()
    db.setup()
    captured = capsys.readouterr()
    assert "Hola" in captured.out
