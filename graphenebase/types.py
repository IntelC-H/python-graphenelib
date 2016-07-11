from binascii import hexlify, unhexlify
import time
from calendar import timegm
from datetime import datetime
import struct
from collections import OrderedDict
import json

from .objecttypes import object_type

timeformat = '%Y-%m-%dT%H:%M:%S%Z'


def varint(n) :
    """ Varint encoding
    """
    data = b''
    while n >= 0x80 :
        data += bytes([(n & 0x7f) | 0x80])
        n >>= 7
    data += bytes([n])
    return data


def varintdecode(data) :
    """ Varint decoding
    """
    shift = 0
    result = 0
    for c in data :
        b = ord(c)
        result |= ((b & 0x7f) << shift)
        if not (b & 0x80) :
            break
        shift += 7
    return result


def variable_buffer(s) :
    """ Encode variable length bugger
    """
    return varint(len(s)) + s


def JsonObj(data) :
    """ Returns json object from data
    """
    return json.loads(str(data))


class Uint8() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<B", self.data)

    def __str__(self) :
        return '%d' % self.data


class Int16() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<h", int(self.data))

    def __str__(self) :
        return '%d' % self.data


class Uint16() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<H", self.data)

    def __str__(self) :
        return '%d' % self.data


class Uint32() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<I", self.data)

    def __str__(self) :
        return '%d' % self.data


class Uint64() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<Q", self.data)

    def __str__(self) :
        return '%d' % self.data


class Varint32() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return varint(self.data)

    def __str__(self) :
        return '%d' % self.data


class Int64() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<q", self.data)

    def __str__(self) :
        return '%d' % self.data


class String() :
    def __init__(self, d) :
        # Repalce UTF8 chars with what ever looks closest
        from unidecode import unidecode
        self.data = unidecode(d)
        # FIXME: Allow for real UTF-8 chars to be used
        # https://github.com/steemit/steem/issues/44

    def __bytes__(self) :
        return varint(len(self.data)) + bytes(self.data, 'utf-8')

    def __str__(self) :
        return '%s' % str(self.data)


class Bytes() :
    def __init__(self, d, length=None) :
        self.data = d
        if length :
            self.length = length
        else :
            self.length = len(self.data)

    def __bytes__(self) :
        # FIXME constraint data to self.length
        d = unhexlify(bytes(self.data, 'utf-8'))
        return varint(len(d)) + d

    def __str__(self) :
        return str(self.data)


class Void() :
    def __init__(self) :
        pass

    def __bytes__(self) :
        return b''

    def __str__(self) :
        return ""


class Array() :
    def __init__(self, d) :
        self.data = d
        self.length = Varint32(len(self.data))

    def __bytes__(self) :
        return bytes(self.length) + b"".join([bytes(a) for a in self.data])

    def __str__(self) :
        r = []
        for a in self.data:
            if isinstance(a, ObjectId):
                r.append(str(a))
            if isinstance(a, VoteId):
                r.append(str(a))
            else:
                r.append(JsonObj(a))
        return json.dumps(r)


class PointInTime() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return struct.pack("<I", timegm(time.strptime((self.data + "UTC"), timeformat)))

    def __str__(self) :
        return self.data


class Signature() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        return self.data

    def __str__(self) :
        return json.dumps(hexlify(self.data).decode('ascii'))


class Bool(Uint8) :  # Bool = Uint8
    def __init__(self, d) :
        super().__init__(d)

    def __str__(self) :
        return True if self.data else False


class Set(Array) :  # Set = Array
    def __init__(self, d) :
        super().__init__(d)


class Fixed_array() :
    def __init__(self, d) :
        raise NotImplementedError

    def __bytes__(self) :
        raise NotImplementedError

    def __str__(self) :
        raise NotImplementedError


class Optional() :
    def __init__(self, d) :
        self.data = d

    def __bytes__(self) :
        if not self.data:
            return bytes(Bool(0))
        else:
            return bytes(Bool(1)) + bytes(self.data) if bytes(self.data) else bytes(Bool(0))

    def __str__(self) :
        return str(self.data)

    def isempty(self) :
        if not self.data:
            return True
        return not bool(bytes(self.data))


class Static_variant() :
    def __init__(self, d, type_id) :
        self.data = d
        self.type_id = type_id

    def __bytes__(self) :
        return varint(self.type_id) + bytes(self.data)

    def __str__(self) :
        return {self._type_id : str(self.data)}


class Map() :
    def __init__(self, data) :
        self.data = data

    def __bytes__(self) :
        b = b""
        b += varint(len(self.data))
        for e in self.data:
            b += bytes(e[0]) + bytes(e[1])
        return b

    def __str__(self) :
        r = []
        for e in self.data:
            r.append([str(e[0]), str(e[1])])
        return json.dumps(r)


class Id() :
    def __init__(self, d) :
        self.data = Varint32(d)

    def __bytes__(self) :
        return bytes(self.data)

    def __str__(self) :
        return str(self.data)


class VoteId():
    def __init__(self, vote) :
        parts = vote.split(":")
        assert len(parts) == 2
        self.type = int(parts[0])
        self.instance = int(parts[1])

    def __bytes__(self) :
        binary = (self.type & 0xff) | (self.instance << 8)
        return struct.pack("<I", binary)

    def __str__(self) :
        return "%d:%d" % (self.type, self.instance)


class ObjectId() :
    """ Encodes object/protocol ids
    """
    def __init__(self, object_str, type_verify=None) :
        if len(object_str.split(".")) == 3 :
            space, type, id = object_str.split(".")
            self.space = int(space)
            self.type = int(type)
            self.instance = Id(int(id))
            self.Id = object_str
            if type_verify :
                assert object_type[type_verify] == int(type),\
                    "Object id does not match object type! " +\
                    "Excpected %d, got %d" %\
                    (object_type[type_verify], int(type))
        else :
            raise Exception("Object id is invalid")

    def __bytes__(self) :
        return bytes(self.instance)  # only yield instance

    def __str__(self) :
        return self.Id
