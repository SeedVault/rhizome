"""JSON Schemas."""

from marshmallow import Schema, fields


class CredentialsSchema(Schema):
    """Credentials schema."""

    username = fields.Str(
        required=True,
        error_messages={'required': 'Username is required.',
                        'null': 'Username is required.'}
    )
    password = fields.String(
        required=True,
        error_messages={'required': 'Password is required.',
                        'null': 'Password is required.'}
    )


class AuthSchema(Schema):
    """Auth schema."""

    status = fields.Str()
    token = fields.Str()


class DotBotSchema(Schema):
    """DotBot schema."""

    id = fields.Str()
    dotbot = fields.Dict()
    organizationId = fields.Str()
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime()


class DotFlowSchema(Schema):
    """DotFlow schema."""

    id = fields.Str()
    dotbotId = fields.Str()
    dotflow = fields.Dict()
    createdAt = fields.DateTime(dump_only=True)
    updatedAt = fields.DateTime()
