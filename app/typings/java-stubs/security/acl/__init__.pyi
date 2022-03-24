import java.lang
import java.security
import java.util
import typing



class AclEntry(java.lang.Cloneable):
    def addPermission(self, permission: 'Permission') -> bool: ...
    def checkPermission(self, permission: 'Permission') -> bool: ...
    def clone(self) -> typing.Any: ...
    def getPrincipal(self) -> java.security.Principal: ...
    def isNegative(self) -> bool: ...
    def permissions(self) -> java.util.Enumeration['Permission']: ...
    def removePermission(self, permission: 'Permission') -> bool: ...
    def setNegativePermissions(self) -> None: ...
    def setPrincipal(self, principal: java.security.Principal) -> bool: ...
    def toString(self) -> str: ...

class AclNotFoundException(java.lang.Exception):
    def __init__(self): ...

class Group(java.security.Principal):
    def addMember(self, principal: java.security.Principal) -> bool: ...
    def equals(self, object: typing.Any) -> bool: ...
    def hashCode(self) -> int: ...
    def isMember(self, principal: java.security.Principal) -> bool: ...
    def members(self) -> java.util.Enumeration[java.security.Principal]: ...
    def removeMember(self, principal: java.security.Principal) -> bool: ...
    def toString(self) -> str: ...

class LastOwnerException(java.lang.Exception):
    def __init__(self): ...

class NotOwnerException(java.lang.Exception):
    def __init__(self): ...

class Owner:
    def addOwner(self, principal: java.security.Principal, principal2: java.security.Principal) -> bool: ...
    def deleteOwner(self, principal: java.security.Principal, principal2: java.security.Principal) -> bool: ...
    def isOwner(self, principal: java.security.Principal) -> bool: ...

class Permission:
    def equals(self, object: typing.Any) -> bool: ...
    def toString(self) -> str: ...

class Acl(Owner):
    def addEntry(self, principal: java.security.Principal, aclEntry: AclEntry) -> bool: ...
    def checkPermission(self, principal: java.security.Principal, permission: Permission) -> bool: ...
    def entries(self) -> java.util.Enumeration[AclEntry]: ...
    def getName(self) -> str: ...
    def getPermissions(self, principal: java.security.Principal) -> java.util.Enumeration[Permission]: ...
    def removeEntry(self, principal: java.security.Principal, aclEntry: AclEntry) -> bool: ...
    def setName(self, principal: java.security.Principal, string: str) -> None: ...
    def toString(self) -> str: ...


class __module_protocol__(typing.Protocol):
    # A module protocol which reflects the result of ``jp.JPackage("java.security.acl")``.

    Acl: typing.Type[Acl]
    AclEntry: typing.Type[AclEntry]
    AclNotFoundException: typing.Type[AclNotFoundException]
    Group: typing.Type[Group]
    LastOwnerException: typing.Type[LastOwnerException]
    NotOwnerException: typing.Type[NotOwnerException]
    Owner: typing.Type[Owner]
    Permission: typing.Type[Permission]
