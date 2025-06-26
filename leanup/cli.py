import click

@click.group()
def main():
    """A command-line interface for LeanUp."""
    pass

@main.group()
def repo():
    """Manage Lean repo installations"""
    pass

