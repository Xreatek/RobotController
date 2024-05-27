from enum import Enum
import pygame
#conn
class ConnType(Enum):
    InternalRoutor = 1
    ExternalRouter = 2
    
class ArmCommands(Enum):
    ArmStill = 0
    ArmGrab = 1
    ArmTransport = 2 
    ArmClose = 3
    ArmOpen = 4
