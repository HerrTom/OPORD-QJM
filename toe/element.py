import logging
from .enums import ElementStatus

class Element:
    def __init__(self, name: str):
        """
        Initialize a new Element.

        Args:
            name (str): The name of the Element.
        """
        # an element is a person or a vehicle in a TO&E role
        self.name   = name
        self.status = ElementStatus.UNDEFINED
        self.assigned_equipment = None
    
    def set_status(self, status: ElementStatus):
        """Set an Element's current status.

        Args:
            status (ElementStatus): New status to set on the Element
        """
        self.status = status

    def assign_equipment(self, nsns: list):
        """
        Assign equipment to the Element. This method should be overridden by subclasses.

        Args:
            nsns (list): List of available NSNs (National Stock Numbers) to choose from.
        """
        logging.error(f'---Attention: Assign_equipemnt is not overwritten for this Element type! {self}')
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name})"
    
class Personnel(Element):
    def __init__(self, name: str, rank: str, equipment: list):
        """
        Initialize a new Element.

        Args:
            name (str): The name of the Element.
        """
        super().__init__(name)
        self.rank = rank  # Specific to Person
        self.equipment = equipment

    def assign_equipment(self, nsns: list):
        """
        Assign equipment to the personnel from the available NSNs.

        Args:
            nsns (list): List of available NSNs (National Stock Numbers) to choose from.
        """
        self.assigned_equipment = []
        for e in self.equipment:
            self.assigned_equipment.append(e.assign_equipment(nsns))

    def __repr__(self):
        return f"Personnel({self.name}. {self.rank})"

class Vehicle(Element):
    # Represents vehicles or crew served weapon roles
    def __init__(self, name: str, equipment: str, crew: list):
        """
        Initialize a new Vehicle element.

        Args:
            name (str): The name of the vehicle.
            equipment (str): The LIN (Line Item Number) of the vehicle this represents.
            crew (list): A list of crew elements assigned to the vehicle.
        """
        super().__init__(name)
        self.equipment = equipment # the LIN of the vehicle this represents
        self.crew = crew # list of elements

    def assign_equipment(self, nsns: list):
        """
        Assign equipment to the vehicle from the available NSNs.

        Args:
            nsns (list): List of available NSNs (National Stock Numbers) to choose from.
        """
        self.assigned_equipment = [self.equipment.assign_equipment(nsns)]
