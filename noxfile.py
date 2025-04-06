import nox


@nox.session(venv_backend="uv")
def lint(session: nox.Session) -> None:
    """
    Run the unit and regular tests.
    """
    _install_dev_deps(session)
    session.run("ruff", "check", *session.posargs)


@nox.session(venv_backend="uv")
def check_format(session: nox.Session) -> None:
    """
    Run the unit and regular tests.
    """
    _install_dev_deps(session)
    session.run("ruff", "format", "--check", *session.posargs)


@nox.session(venv_backend="uv")
def format(session: nox.Session) -> None:
    """
    Run the unit and regular tests.
    """
    _install_dev_deps(session)
    session.run("ruff", "format", *session.posargs)


@nox.session(venv_backend="uv")
def fix(session: nox.Session) -> None:
    """Fix formatting and linting"""
    _install_dev_deps(session)
    session.run("ruff", "check", "--fix")
    session.run("ruff", "format")


def _install_dev_deps(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--only-dev",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
