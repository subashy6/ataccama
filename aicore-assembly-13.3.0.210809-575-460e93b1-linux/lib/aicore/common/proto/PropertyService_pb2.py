# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: PropertyService.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='PropertyService.proto',
  package='com.ataccama.one.onecfg.server.grpc',
  syntax='proto3',
  serialized_options=b'P\001',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x15PropertyService.proto\x12#com.ataccama.one.onecfg.server.grpc\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1fgoogle/protobuf/timestamp.proto\"D\n\x0fPropertyRequest\x12\x14\n\x0c\x64\x65ploymentId\x18\x01 \x01(\x05\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\r\n\x05value\x18\x03 \x01(\t\"\xa6\x02\n\x15GetPropertiesResponse\x12W\n\nproperties\x18\x01 \x03(\x0b\x32\x43.com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property\x12\x0f\n\x07version\x18\x02 \x01(\t\x1a\xa2\x01\n\x08Property\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\x12V\n\x04type\x18\x03 \x01(\x0e\x32H.com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property.Type\"!\n\x04Type\x12\x0b\n\x07RUNTIME\x10\x00\x12\x0c\n\x08PLATFORM\x10\x01\"+\n\x18GetLatestVersionResponse\x12\x0f\n\x07version\x18\x01 \x01(\t\"F\n\x18PropertiesAppliedRequest\x12\x19\n\x11replicaIdentifier\x18\x01 \x01(\t\x12\x0f\n\x07version\x18\x02 \x01(\t\"2\n\x15NothingToApplyRequest\x12\x19\n\x11replicaIdentifier\x18\x01 \x01(\t2\xa9\x03\n\x0fPropertyService\x12i\n\x10getLatestVersion\x12\x16.google.protobuf.Empty\x1a=.com.ataccama.one.onecfg.server.grpc.GetLatestVersionResponse\x12\x63\n\rgetProperties\x12\x16.google.protobuf.Empty\x1a:.com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse\x12`\n\x07\x61pplied\x12=.com.ataccama.one.onecfg.server.grpc.PropertiesAppliedRequest\x1a\x16.google.protobuf.Empty\x12\x64\n\x0enothingToApply\x12:.com.ataccama.one.onecfg.server.grpc.NothingToApplyRequest\x1a\x16.google.protobuf.EmptyB\x02P\x01\x62\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_empty__pb2.DESCRIPTOR,google_dot_protobuf_dot_timestamp__pb2.DESCRIPTOR,])



_GETPROPERTIESRESPONSE_PROPERTY_TYPE = _descriptor.EnumDescriptor(
  name='Type',
  full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property.Type',
  filename=None,
  file=DESCRIPTOR,
  create_key=_descriptor._internal_create_key,
  values=[
    _descriptor.EnumValueDescriptor(
      name='RUNTIME', index=0, number=0,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
    _descriptor.EnumValueDescriptor(
      name='PLATFORM', index=1, number=1,
      serialized_options=None,
      type=None,
      create_key=_descriptor._internal_create_key),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=456,
  serialized_end=489,
)
_sym_db.RegisterEnumDescriptor(_GETPROPERTIESRESPONSE_PROPERTY_TYPE)


_PROPERTYREQUEST = _descriptor.Descriptor(
  name='PropertyRequest',
  full_name='com.ataccama.one.onecfg.server.grpc.PropertyRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='deploymentId', full_name='com.ataccama.one.onecfg.server.grpc.PropertyRequest.deploymentId', index=0,
      number=1, type=5, cpp_type=1, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='name', full_name='com.ataccama.one.onecfg.server.grpc.PropertyRequest.name', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='com.ataccama.one.onecfg.server.grpc.PropertyRequest.value', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=124,
  serialized_end=192,
)


_GETPROPERTIESRESPONSE_PROPERTY = _descriptor.Descriptor(
  name='Property',
  full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='type', full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property.type', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _GETPROPERTIESRESPONSE_PROPERTY_TYPE,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=327,
  serialized_end=489,
)

_GETPROPERTIESRESPONSE = _descriptor.Descriptor(
  name='GetPropertiesResponse',
  full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='properties', full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.properties', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='version', full_name='com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.version', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_GETPROPERTIESRESPONSE_PROPERTY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=195,
  serialized_end=489,
)


_GETLATESTVERSIONRESPONSE = _descriptor.Descriptor(
  name='GetLatestVersionResponse',
  full_name='com.ataccama.one.onecfg.server.grpc.GetLatestVersionResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='version', full_name='com.ataccama.one.onecfg.server.grpc.GetLatestVersionResponse.version', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=491,
  serialized_end=534,
)


_PROPERTIESAPPLIEDREQUEST = _descriptor.Descriptor(
  name='PropertiesAppliedRequest',
  full_name='com.ataccama.one.onecfg.server.grpc.PropertiesAppliedRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='replicaIdentifier', full_name='com.ataccama.one.onecfg.server.grpc.PropertiesAppliedRequest.replicaIdentifier', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='version', full_name='com.ataccama.one.onecfg.server.grpc.PropertiesAppliedRequest.version', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=536,
  serialized_end=606,
)


_NOTHINGTOAPPLYREQUEST = _descriptor.Descriptor(
  name='NothingToApplyRequest',
  full_name='com.ataccama.one.onecfg.server.grpc.NothingToApplyRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='replicaIdentifier', full_name='com.ataccama.one.onecfg.server.grpc.NothingToApplyRequest.replicaIdentifier', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=608,
  serialized_end=658,
)

_GETPROPERTIESRESPONSE_PROPERTY.fields_by_name['type'].enum_type = _GETPROPERTIESRESPONSE_PROPERTY_TYPE
_GETPROPERTIESRESPONSE_PROPERTY.containing_type = _GETPROPERTIESRESPONSE
_GETPROPERTIESRESPONSE_PROPERTY_TYPE.containing_type = _GETPROPERTIESRESPONSE_PROPERTY
_GETPROPERTIESRESPONSE.fields_by_name['properties'].message_type = _GETPROPERTIESRESPONSE_PROPERTY
DESCRIPTOR.message_types_by_name['PropertyRequest'] = _PROPERTYREQUEST
DESCRIPTOR.message_types_by_name['GetPropertiesResponse'] = _GETPROPERTIESRESPONSE
DESCRIPTOR.message_types_by_name['GetLatestVersionResponse'] = _GETLATESTVERSIONRESPONSE
DESCRIPTOR.message_types_by_name['PropertiesAppliedRequest'] = _PROPERTIESAPPLIEDREQUEST
DESCRIPTOR.message_types_by_name['NothingToApplyRequest'] = _NOTHINGTOAPPLYREQUEST
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

PropertyRequest = _reflection.GeneratedProtocolMessageType('PropertyRequest', (_message.Message,), {
  'DESCRIPTOR' : _PROPERTYREQUEST,
  '__module__' : 'PropertyService_pb2'
  # @@protoc_insertion_point(class_scope:com.ataccama.one.onecfg.server.grpc.PropertyRequest)
  })
_sym_db.RegisterMessage(PropertyRequest)

GetPropertiesResponse = _reflection.GeneratedProtocolMessageType('GetPropertiesResponse', (_message.Message,), {

  'Property' : _reflection.GeneratedProtocolMessageType('Property', (_message.Message,), {
    'DESCRIPTOR' : _GETPROPERTIESRESPONSE_PROPERTY,
    '__module__' : 'PropertyService_pb2'
    # @@protoc_insertion_point(class_scope:com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse.Property)
    })
  ,
  'DESCRIPTOR' : _GETPROPERTIESRESPONSE,
  '__module__' : 'PropertyService_pb2'
  # @@protoc_insertion_point(class_scope:com.ataccama.one.onecfg.server.grpc.GetPropertiesResponse)
  })
_sym_db.RegisterMessage(GetPropertiesResponse)
_sym_db.RegisterMessage(GetPropertiesResponse.Property)

GetLatestVersionResponse = _reflection.GeneratedProtocolMessageType('GetLatestVersionResponse', (_message.Message,), {
  'DESCRIPTOR' : _GETLATESTVERSIONRESPONSE,
  '__module__' : 'PropertyService_pb2'
  # @@protoc_insertion_point(class_scope:com.ataccama.one.onecfg.server.grpc.GetLatestVersionResponse)
  })
_sym_db.RegisterMessage(GetLatestVersionResponse)

PropertiesAppliedRequest = _reflection.GeneratedProtocolMessageType('PropertiesAppliedRequest', (_message.Message,), {
  'DESCRIPTOR' : _PROPERTIESAPPLIEDREQUEST,
  '__module__' : 'PropertyService_pb2'
  # @@protoc_insertion_point(class_scope:com.ataccama.one.onecfg.server.grpc.PropertiesAppliedRequest)
  })
_sym_db.RegisterMessage(PropertiesAppliedRequest)

NothingToApplyRequest = _reflection.GeneratedProtocolMessageType('NothingToApplyRequest', (_message.Message,), {
  'DESCRIPTOR' : _NOTHINGTOAPPLYREQUEST,
  '__module__' : 'PropertyService_pb2'
  # @@protoc_insertion_point(class_scope:com.ataccama.one.onecfg.server.grpc.NothingToApplyRequest)
  })
_sym_db.RegisterMessage(NothingToApplyRequest)


DESCRIPTOR._options = None

_PROPERTYSERVICE = _descriptor.ServiceDescriptor(
  name='PropertyService',
  full_name='com.ataccama.one.onecfg.server.grpc.PropertyService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=661,
  serialized_end=1086,
  methods=[
  _descriptor.MethodDescriptor(
    name='getLatestVersion',
    full_name='com.ataccama.one.onecfg.server.grpc.PropertyService.getLatestVersion',
    index=0,
    containing_service=None,
    input_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    output_type=_GETLATESTVERSIONRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='getProperties',
    full_name='com.ataccama.one.onecfg.server.grpc.PropertyService.getProperties',
    index=1,
    containing_service=None,
    input_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    output_type=_GETPROPERTIESRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='applied',
    full_name='com.ataccama.one.onecfg.server.grpc.PropertyService.applied',
    index=2,
    containing_service=None,
    input_type=_PROPERTIESAPPLIEDREQUEST,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='nothingToApply',
    full_name='com.ataccama.one.onecfg.server.grpc.PropertyService.nothingToApply',
    index=3,
    containing_service=None,
    input_type=_NOTHINGTOAPPLYREQUEST,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_PROPERTYSERVICE)

DESCRIPTOR.services_by_name['PropertyService'] = _PROPERTYSERVICE

# @@protoc_insertion_point(module_scope)
