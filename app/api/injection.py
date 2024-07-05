"""Dependency injection для роботи API."""

import fastapi

from app.internal import docx, storage, template


def get_file_storage() -> storage.Storage:
    return storage.LocalStorage()


def get_tmp_storage() -> storage.Storage:
    return storage.LocalStorage()


def get_validator(
    file_storage: storage.Storage = fastapi.Depends(get_file_storage),
) -> template.TemplateValidator:
    return template.StorageTemplateValidator(file_storage)


def get_tmp_validator(
    tmp_storage: storage.Storage = fastapi.Depends(get_tmp_storage),
) -> template.TemplateValidator:
    return template.StorageTemplateValidator(tmp_storage)


def get_factory(
    file_storage: storage.Storage = fastapi.Depends(get_file_storage),
    validator: template.TemplateValidator = fastapi.Depends(get_validator),
) -> template.TemplateFactory:
    return template.StorageTemplateFactory(file_storage, validator)


def get_cache() -> template.TemplateCache:
    return template.MemoryTemplateCache()


def get_repo(
    file_storage: storage.LocalStorage = fastapi.Depends(get_file_storage),
    tmp_storage: storage.LocalStorage = fastapi.Depends(get_tmp_storage),
    tmp_validator: template.TemplateValidator = fastapi.Depends(
        get_tmp_validator
    ),
    cache: template.MemoryTemplateCache = fastapi.Depends(get_cache),
    factory: template.TemplateFactory = fastapi.Depends(get_factory),
) -> template.TemplateRepository:
    return template.StorageTemplateRepository(
        file_storage, tmp_storage, tmp_validator, cache, factory
    )


def get_generator(
    file_storage: storage.LocalStorage = fastapi.Depends(get_file_storage),
) -> docx.DocxGenerator:
    return docx.DoctplDocxGenerator(file_storage)
