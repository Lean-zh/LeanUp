import click

@click.group()
def leanup():
    """A command-line interface for LeanUp."""
    pass

@leanup.group()
def repo():
    """Manage Lean repo installations"""
    pass

