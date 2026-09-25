import kagura


def test_project_layout() -> None:
    assert (kagura.ROOT / "pyproject.toml").exists()
    assert kagura.DATA_RAW.is_dir()
    assert kagura.DATA_PROCESSED.is_dir()
    assert kagura.FIGURES.is_dir()
