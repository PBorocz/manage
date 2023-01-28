import json
from pathlib import Path

import pytest
import toml
from manage.models import Configuration, Step, Recipe, Recipes


@pytest.fixture
def path_():
    path = Path("/tmp/test_model.toml")
    yield path
    if path.exists():
        path.unlink()


def test_model_roundtrip(path_: Path):
    """Confirm that we can 'persist' Recipes to toml and get them exactly back."""
    s1 = Step(method="clean_1")
    s2 = Step(step="clean_2", config=True, echo_stdout=True, allow_error=True, quiet_mode=True)
    s3 = Step(method="build")
    r1 = Recipe(id_="doClean", name="Do Clean", description="A Description", steps=[s1,s2])
    r2 = Recipe(id_="doBuild", name="Do Build", description="Another Description", steps=[s3,])
    rs = Recipes(recipes=[r1,r2])

    # Dump out:
    path_.write_text(toml.dumps(json.loads(rs.json())))

    # Confirm that what we get back is identical:
    assert rs == Recipes(**toml.loads(path_.read_text()))

    
