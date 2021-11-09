# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: common.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='common.proto',
  package='ataccama.aicore.common',
  syntax='proto3',
  serialized_options=b'\n$com.ataccama.one.aicore.common.protoP\001',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x0c\x63ommon.proto\x12\x16\x61taccama.aicore.common\"\x18\n\x16ShutdownServiceRequest\"\x19\n\x17ShutdownServiceResponse\"\x1b\n\x0bTestRequest\x12\x0c\n\x04\x64\x61ta\x18\x01 \x01(\t\"#\n\x0cTestResponse\x12\x13\n\x0b\x65\x63hoed_data\x18\x01 \x01(\t2\x86\x01\n\x0e\x43ommonMessages\x12t\n\x0fShutdownService\x12..ataccama.aicore.common.ShutdownServiceRequest\x1a/.ataccama.aicore.common.ShutdownServiceResponse\"\x00\x32g\n\x0cTestMessages\x12W\n\x04Test\x12#.ataccama.aicore.common.TestRequest\x1a$.ataccama.aicore.common.TestResponse\"\x00(\x01\x30\x01\x42(\n$com.ataccama.one.aicore.common.protoP\x01\x62\x06proto3'
)




_SHUTDOWNSERVICEREQUEST = _descriptor.Descriptor(
  name='ShutdownServiceRequest',
  full_name='ataccama.aicore.common.ShutdownServiceRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
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
  serialized_start=40,
  serialized_end=64,
)


_SHUTDOWNSERVICERESPONSE = _descriptor.Descriptor(
  name='ShutdownServiceResponse',
  full_name='ataccama.aicore.common.ShutdownServiceResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
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
  serialized_start=66,
  serialized_end=91,
)


_TESTREQUEST = _descriptor.Descriptor(
  name='TestRequest',
  full_name='ataccama.aicore.common.TestRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='data', full_name='ataccama.aicore.common.TestRequest.data', index=0,
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
  serialized_start=93,
  serialized_end=120,
)


_TESTRESPONSE = _descriptor.Descriptor(
  name='TestResponse',
  full_name='ataccama.aicore.common.TestResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='echoed_data', full_name='ataccama.aicore.common.TestResponse.echoed_data', index=0,
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
  serialized_start=122,
  serialized_end=157,
)

DESCRIPTOR.message_types_by_name['ShutdownServiceRequest'] = _SHUTDOWNSERVICEREQUEST
DESCRIPTOR.message_types_by_name['ShutdownServiceResponse'] = _SHUTDOWNSERVICERESPONSE
DESCRIPTOR.message_types_by_name['TestRequest'] = _TESTREQUEST
DESCRIPTOR.message_types_by_name['TestResponse'] = _TESTRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

ShutdownServiceRequest = _reflection.GeneratedProtocolMessageType('ShutdownServiceRequest', (_message.Message,), {
  'DESCRIPTOR' : _SHUTDOWNSERVICEREQUEST,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:ataccama.aicore.common.ShutdownServiceRequest)
  })
_sym_db.RegisterMessage(ShutdownServiceRequest)

ShutdownServiceResponse = _reflection.GeneratedProtocolMessageType('ShutdownServiceResponse', (_message.Message,), {
  'DESCRIPTOR' : _SHUTDOWNSERVICERESPONSE,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:ataccama.aicore.common.ShutdownServiceResponse)
  })
_sym_db.RegisterMessage(ShutdownServiceResponse)

TestRequest = _reflection.GeneratedProtocolMessageType('TestRequest', (_message.Message,), {
  'DESCRIPTOR' : _TESTREQUEST,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:ataccama.aicore.common.TestRequest)
  })
_sym_db.RegisterMessage(TestRequest)

TestResponse = _reflection.GeneratedProtocolMessageType('TestResponse', (_message.Message,), {
  'DESCRIPTOR' : _TESTRESPONSE,
  '__module__' : 'common_pb2'
  # @@protoc_insertion_point(class_scope:ataccama.aicore.common.TestResponse)
  })
_sym_db.RegisterMessage(TestResponse)


DESCRIPTOR._options = None

_COMMONMESSAGES = _descriptor.ServiceDescriptor(
  name='CommonMessages',
  full_name='ataccama.aicore.common.CommonMessages',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=160,
  serialized_end=294,
  methods=[
  _descriptor.MethodDescriptor(
    name='ShutdownService',
    full_name='ataccama.aicore.common.CommonMessages.ShutdownService',
    index=0,
    containing_service=None,
    input_type=_SHUTDOWNSERVICEREQUEST,
    output_type=_SHUTDOWNSERVICERESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_COMMONMESSAGES)

DESCRIPTOR.services_by_name['CommonMessages'] = _COMMONMESSAGES


_TESTMESSAGES = _descriptor.ServiceDescriptor(
  name='TestMessages',
  full_name='ataccama.aicore.common.TestMessages',
  file=DESCRIPTOR,
  index=1,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=296,
  serialized_end=399,
  methods=[
  _descriptor.MethodDescriptor(
    name='Test',
    full_name='ataccama.aicore.common.TestMessages.Test',
    index=0,
    containing_service=None,
    input_type=_TESTREQUEST,
    output_type=_TESTRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_TESTMESSAGES)

DESCRIPTOR.services_by_name['TestMessages'] = _TESTMESSAGES

# @@protoc_insertion_point(module_scope)