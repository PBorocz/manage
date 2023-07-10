from rich import print

from manage.models import Configuration, Recipes, Recipe, Step


def main(configuration: Configuration, recipes: Recipes, step: dict) -> bool:
    """Show the recipes."""
    print("[yellow]The following recipes are currently defined (items in [bold]bold[/] differ from default!):")
    for id_, recipe in recipes:
        print_recipe(id_, recipes, recipe)
    return True

def print_recipe(id_: str, recipes: Recipes, recipe: Recipe, indent_level: int = 0) -> None:
    """Print a recipe."""
    indent = " " * indent_level
    print(f"{indent}[bold italic]{id_}[/] ≫ {recipe.description}")
    for step in recipe:
        if step.method:
            print_step(step, indent_level + 2)
        else:
            sub_recipe = recipes.get(step.recipe)
            print_recipe(step.recipe, recipes, sub_recipe, indent_level + 4)


def print_step(step: Step, indent_level: int) -> None:
    """Print the step (only a method one)."""
    indent = " " * indent_level
    print(f"{indent}• [bold]{step.method}[/] method")

    indent += " " * 2  # Indent one level deeper for step attributes

    # Highlight (by bolding) attributes that are DIFFERENT from their default in manage/models.py.
    (pre, post) = ("[bold]", "[/]") if not step.confirm else ("", "")
    print(f"{indent}{pre}confirm     : {step.confirm}{post}")

    (pre, post) = ("[bold]", "[/]") if step.echo_stdout else ("", "")
    print(f"{indent}{pre}echo_stdout : {step.echo_stdout}{post}")

    (pre, post) = ("[bold]", "[/]") if step.allow_error else ("", "")
    print(f"{indent}{pre}allow_error : {step.allow_error}{post}")

    (pre, post) = ("[bold]", "[/]") if step.quiet_mode else ("", "")
    print(f"{indent}{pre}quiet_mode  : {step.quiet_mode}{post}")

    # Put out any arguments the step might have:
    for arg_name, arg_value in step.arguments.items():
        print(f"{indent}{arg_name:11s} : {arg_value}")
