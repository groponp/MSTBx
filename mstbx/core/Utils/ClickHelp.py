"""Shared helper to render ``--help`` with options grouped by section.

Click's ``epilog=`` is plain prose: the default formatter rewraps it to the
terminal width and destroys any manual line breaks or indentation, so it
cannot be used to hand-draw a table of option groups. The correct way to
group options in Click is to override ``Command.format_options`` and place
each parameter into its own ``formatter.section(...)`` block, which is what
this module does generically for any command.
"""

import click


def explicit(ctx, name):
    """True only if the user typed this flag, not if it came from its default.

    Needed to reject flag combinations that would otherwise be silently
    ignored: an option with a ``default=`` looks identical to one the user
    never mentioned unless checked against its Click parameter source.
    """
    return ctx.get_parameter_source(name) == click.core.ParameterSource.COMMANDLINE


def grouped_command(groups, other_title="Other Options"):
    """Build a ``click.Command`` subclass whose ``--help`` groups options.

    Parameters
    ----------
    groups : dict[str, list[str]]
        Ordered mapping of section title to the Click parameter names
        (the Python argument name, e.g. ``fix_structure`` for
        ``--fix-structure``) that belong in that section.
    other_title : str
        Section title used for any parameter not listed in ``groups``
        (for example ``--help`` itself, or an option added later and
        not yet classified).
    """

    class _GroupedHelpCommand(click.Command):
        def format_options(self, ctx, formatter):
            seen = set()
            for title, names in groups.items():
                records = []
                for param in self.get_params(ctx):
                    if param.name in names:
                        record = param.get_help_record(ctx)
                        if record:
                            records.append(record)
                            seen.add(param.name)
                if records:
                    with formatter.section(title):
                        formatter.write_dl(records)

            leftover = [
                record
                for param in self.get_params(ctx)
                if param.name not in seen
                for record in [param.get_help_record(ctx)]
                if record
            ]
            if leftover:
                with formatter.section(other_title):
                    formatter.write_dl(leftover)

    return _GroupedHelpCommand
