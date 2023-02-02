from rich import print

from manage.models import Configuration, Recipes, Recipe, Step


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Show the recipes."""
    print("\nThe following recipes are currently defined (items in [bold]bold[/] differ from default!):")
    for id_, recipe in recipes.items():
        print_recipe(id_, recipe)
    return True

def print_recipe(id_: str, recipe: Recipe) -> None:
    print(f"\n[bold italic]{id_}[/] ≫ {recipe.description}")
    for step in recipe:
        print_step(step)

def print_step(step: Step) -> None:
    indent = " " * 2
    if step.method:
        print(f"{indent}• [bold]{step.method}[/] method")
    else:
        print(f"{indent}• [bold]{step.step}[/] step!")

    indent += " " * 2

    (pre, post) = ("[bold]", "[/]") if not step.confirm else ("", "")
    print(f"{indent}{pre}confirm{post}     : {pre}{step.confirm}{post}")

    (pre, post) = ("[bold]", "[/]") if step.echo_stdout else ("", "")
    print(f"{indent}{pre}echo_stdout{post} : {pre}{step.echo_stdout}{post}")

    (pre, post) = ("[bold]", "[/]") if step.allow_error else ("", "")
    print(f"{indent}{pre}allow_error{post} : {pre}{step.allow_error}{post}")

    (pre, post) = ("[bold]", "[/]") if step.quiet_mode else ("", "")
    print(f"{indent}{pre}quiet_mode{post}  : {pre}{step.quiet_mode}{post}")

    for arg_name, arg_value in step.args_.items():
        print(f"{indent}{arg_name:11s} : {arg_value}")
