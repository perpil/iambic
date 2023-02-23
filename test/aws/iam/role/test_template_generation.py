from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from iambic.core.iambic_enum import IambicManaged
from iambic.plugins.v0_1_0.aws.iam.role.models import RoleTemplate
from iambic.plugins.v0_1_0.aws.iam.role.template_generation import create_templated_role
from iambic.plugins.v0_1_0.aws.models import AWSAccount


@pytest.fixture
def test_role():
    test_role_name = "test_role"
    test_role = RoleTemplate(
        identifier=test_role_name,
        included_accounts=["dev"],
        file_path="/tmp/test_role.yaml",
        properties={"role_name": test_role_name},
    )
    return test_role


@pytest.fixture
def mock_account_id_to_role_map(test_role):
    with patch(
        "iambic.plugins.v0_1_0.aws.iam.role.template_generation._account_id_to_role_map"
    ) as _mock_account_id_to_role_map:
        async_mock = AsyncMock(return_value={"dev": test_role.properties.dict()})
        _mock_account_id_to_role_map.side_effect = async_mock
        yield _mock_account_id_to_role_map


@pytest.fixture
def mock_write():
    with patch("iambic.core.models.BaseTemplate.write") as _mock_write:
        yield _mock_write


@pytest.mark.asyncio
async def test_create_template_role(
    test_config, test_role, mock_account_id_to_role_map, mock_write
):
    test_account_id = "123456789012"
    test_account = AWSAccount(
        account_id=test_account_id, account_name="dev", assume_role_arn=""
    )
    test_aws_account_map = {
        test_account.account_name: test_account,
        test_account.account_id: test_account,
    }
    test_role_name = "test_role"
    test_role_dir = ""
    test_role_ref = test_role.properties.dict()
    test_role_ref["account_id"] = "123456789012"
    test_role_refs = [test_role_ref]
    test_existing_template_map = {}

    output_role = await create_templated_role(
        test_aws_account_map,
        test_role_name,
        test_role_refs,
        test_role_dir,
        test_existing_template_map,
        test_config.aws,
    )
    assert output_role.iambic_managed is IambicManaged.UNDEFINED

    test_role.iambic_managed = IambicManaged.READ_AND_WRITE
    test_existing_template_map = {test_role_name: test_role}
    output_role = await create_templated_role(
        test_aws_account_map,
        test_role_name,
        test_role_refs,
        test_role_dir,
        test_existing_template_map,
        test_config.aws,
    )
    assert output_role.iambic_managed is IambicManaged.READ_AND_WRITE
