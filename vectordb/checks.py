from django.core.checks import Tags, Warning, register


@register(Tags.compatibility)
def embedding_system_check(app_configs, **kwargs):
    errors = []
    from vectordb.settings import vectordb_settings

    if (
        vectordb_settings.DEFAULT_EMBEDDING_CLASS
        and not vectordb_settings.DEFAULT_EMBEDDING_DIMENSION
    ):
        errors.append(
            Warning(
                "You have specified a default DEFAULT_EMBEDDING_CLASS for vectordb setting, "
                "without specifying also a DEFAULT_EMBEDDING_DIMENSION.",
                id="vectordb.W001",
            )
        )
    return errors
