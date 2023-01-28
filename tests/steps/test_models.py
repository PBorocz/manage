import json
from pathlib import Path

import pytest
import toml
from manage.models import Step, Recipe, Recipes


@pytest.fixture
def path_():
    path = Path("/tmp/test_model.toml")
    yield path
    if path.exists():
        path.unlink()


def test_model_roundtrip(path_: Path):
    """Confirm that we can 'persist' Recipes to toml and get them exactly back."""

    s1 = Step(method="clean_method")
    s2 = Step(step="clean_step", config=True, echo_stdout=True, allow_error=True, quiet_mode=True)
    r1 = Recipe(name="Do Clean", description="A Description", steps=[s1, s2])

    s3 = Step(method="build")
    r2 = Recipe(name="Do Build", description="Another Description", steps=[s3,])

    recipes_built = Recipes(recipes={
        "clean" : r1,
        "build" : r2,
    })

    # Dump out:
    # (ref: https://github.com/pydantic/pydantic/discussions/4013 as we can't directly send pydantic to toml :-(
    path_.write_text(toml.dumps(json.loads(recipes_built.json())))

    # Confirm That we *can* go round-trip (even though we don't actually need to on a day-to-day basis)
    recipes_parsed = Recipes(**toml.loads(path_.read_text()))
    assert recipes_built == recipes_parsed

    if False:
        from rich import print
        for recipe in recipes_parsed:
            print(recipe)
