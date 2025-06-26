import os
import pytest
from pathlib import Path
import tempfile
from leanup.const import OS_TYPE
from leanup.utils.executor import CommandExecutor

def test_basic_execute(executor:CommandExecutor):
    """Test basic command execution"""
    cmd = ['echo', 'hello']
    
    output, error, code = executor.execute(cmd)
    assert code == 0
    assert 'hello' in output
    assert error == ''

def test_execute_with_error(executor:CommandExecutor):
    """Test command execution with error"""
    if OS_TYPE == 'Windows':
        cmd = ['dir', '/invalid_path']
    else:
        cmd = ['ls', '/nonexistent_directory']
    
    output, error, code = executor.execute(cmd)
    assert code != 0
    assert error != ''

def test_working_directory(executor:CommandExecutor, temp_dir:Path):
    """Test working directory context manager"""
    test_file = temp_dir / 'test.txt'
    test_file.write_text('test content')

    with executor.working_directory(temp_dir, chdir=True):
        if OS_TYPE == 'Windows':
            cmd = ['dir']
        else:
            cmd = ['ls']
        output, error, code = executor.execute(cmd)
        assert code == 0
        assert 'test.txt' in output

def test_execute_in_directory(executor:CommandExecutor, temp_dir:Path):
    """Test execute_in_directory method"""
    test_file = temp_dir / 'test.txt'
    test_file.write_text('test content')

    if OS_TYPE == 'Windows':
        cmd = ['dir']
    else:
        cmd = ['ls']
    
    output, error, code = executor.execute_in_directory(cmd, directory=temp_dir)
    assert code == 0
    assert 'test.txt' in output

def test_timeout(executor:CommandExecutor):
    """Test command execution with timeout"""
    if OS_TYPE == 'Windows':
        cmd = ['timeout', '10']
    else:
        cmd = ['sleep', '10']
    
    output, error, code = executor.execute(cmd, timeout=1)
    assert code != 0


def test_multiple_commands(executor:CommandExecutor):
    """Test executing multiple commands sequentially"""
    commands = []
    if OS_TYPE == 'Windows':
        commands = [
            ['echo', 'first'],
            ['echo', 'second'],
        ]
    else:
        commands = [
            ['echo', 'first'],
            ['echo', 'second'],
        ]
    
    results = []
    for cmd in commands:
        output, error, code = executor.execute(cmd)
        results.append((output, code))
    
    assert all(code == 0 for _, code in results)
    assert 'first' in results[0][0]
    assert 'second' in results[1][0]