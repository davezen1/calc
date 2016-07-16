import os
import subprocess
import djclick as click


def get_tap_errors(result):
    return [line for line in result.split(os.linesep)
            if line.startswith('not ok')]


@click.command()
@click.option('--verbose', is_flag=True)
def command(verbose):
    tests = [
        {'name': 'py.test', 'cmd': 'py.test --tap-stream'},
        # TODO: tap output for flake8 (pyflakes and pep8)?
        # {'name': 'flake8',  'cmd': 'flake8 --exclude=node_modules .'},
        {'name': 'eslint',  'cmd': 'npm run tap-eslint'},
    ]

    for entry in tests:
        click.echo('-> {} '.format(entry['name']), nl=False)
        result = subprocess.check_output(
            entry['cmd'], stderr=subprocess.STDOUT, shell=True).decode('utf-8')

        errors = get_tap_errors(result)
        if (len(errors) is 0):
            click.secho('\tOK', fg='green')
        else:
            click.secho('\tFAIL', fg='red')

        if not verbose:
            # only print errors
            for e in errors:
                click.echo(e)
        else:
            print(result)
