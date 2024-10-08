import logging
from random import random
from .enums import ElementStatus
from qjm import (EquipmentOLICategory, VehicleCategory,
                   CasualtyRates, LossRateFactors,
                   RecoveryRatesAttacker, RecoveryRatesDefender,
                   FormationOLI)


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
        self.qjm_equipment = None
    
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

    
    def assign_qjm_equipment(self, edb):
        """
        Assign equipment to the vehicle from the QJM database.

        Args:
            edb (EquipmentDatabase): The EquipmentDatabase object to use for equipment assignment.
        """
        for e in self.assigned_equipment:
            qjm_equip = edb.get_vehicle(e)
            if qjm_equip is None:
                # Search the weapons database if not found in vehicles
                qjm_equip = edb.get_weapon(e)
            if qjm_equip is None:
                # if still not found, log a warning
                logging.warning(f'{e} not found in database!')
            self.qjm_equipment.append(qjm_equip)

    def get_qjm_equipment(self,):
        return self.qjm_equipment

    def get_oli(self):
        oli = FormationOLI()
        for e in self.qjm_equipment:
            if e is not None:
                logging.debug(f'Element {self.name} has equipment {e.name} with OLI {e.q_OLI}')
                if e.oli_category == EquipmentOLICategory.small_arms:
                    oli.small_arms = e.q_OLI
                elif e.oli_category == EquipmentOLICategory.heavy_weapon:
                    oli.heavy_weapons = e.q_OLI
                elif e.oli_category == EquipmentOLICategory.antitank:
                    oli.antitank = e.q_OLI
                elif e.oli_category == EquipmentOLICategory.artillery:
                    oli.artillery = e.q_OLI
                elif e.oli_category == EquipmentOLICategory.antiair:
                    oli.antiair = e.q_OLI
                elif e.oli_category == EquipmentOLICategory.armour:
                    oli.armour = e.q_OLI
                elif e.oli_category == EquipmentOLICategory.aircraft:
                    oli.aircraft = e.q_OLI
        logging.debug(f'Element {self.name} has OLI {oli}')
        return oli

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
        self.qjm_equipment = []

    def assign_equipment(self, nsns: list):
        """
        Assign equipment to the personnel from the available NSNs.

        Args:
            nsns (list): List of available NSNs (National Stock Numbers) to choose from.
        """
        self.assigned_equipment = []
        for e in self.equipment:
            self.assigned_equipment.append(e.assign_equipment(nsns))

    def test_casualty(self, cr):
        """Test if this personnel is killed or not.

        Args:
            cr (CasualtyRates): Casualty rates object from the battle resolution
        """
        if cr.attacker:
            rr = RecoveryRatesAttacker()
        else:
            rr = RecoveryRatesDefender()
        
        # Personnel always just use the CR for personnel
        cr_total = cr.personnel

        # test if the personnel is hit
        if random() < cr_total:
            # personnel is hit
            if random() < rr.personnel:
                # personnel is wounded, use DAMAGED for wounded
                self.status = ElementStatus.DAMAGED
                logging.debug(f'{self} is wounded')
            else:
                # personnel is killed, use DESTROYED for killed
                self.status = ElementStatus.DESTROYED
                logging.debug(f'{self} is destroyed')

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
        self.qjm_equipment = []

    def assign_equipment(self, nsns: list):
        """
        Assign equipment to the vehicle from the available NSNs.

        Args:
            nsns (list): List of available NSNs (National Stock Numbers) to choose from.
        """
        self.assigned_equipment = [self.equipment.assign_equipment(nsns)]


    def test_casualty(self, cr):
        """Test if this vehicle is destroyed or not.

        Args:
            cr (CasualtyRates): Casualty rates object from the battle resolution
        """
        if cr.attacker:
            rr = RecoveryRatesAttacker()
        else:
            rr = RecoveryRatesDefender()
        for e in self.qjm_equipment:
            if e is not None:
                if e.qjm_vehicle_category == VehicleCategory.tank:
                    loss_rate_factor = LossRateFactors.tanks
                    recovery_rate = rr.tanks
                    cr_total = cr.armour * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.armoured_car:
                    loss_rate_factor = LossRateFactors.apc
                    recovery_rate = rr.apc
                    cr_total = cr.personnel * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.truck:
                    loss_rate_factor = LossRateFactors.vehicles
                    recovery_rate = rr.vehicles
                    cr_total = cr.personnel * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.artillery:
                    loss_rate_factor = LossRateFactors.artillery_self_propelled
                    recovery_rate = rr.artillery_self_propelled
                    cr_total = cr.artillery * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.arv:
                    loss_rate_factor = LossRateFactors.artillery_self_propelled
                    recovery_rate = rr.vehicles
                    cr_total = cr.personnel * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.ifv:
                    loss_rate_factor = LossRateFactors.tanks
                    recovery_rate = rr.tanks
                    cr_total = cr.armour * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.apc:
                    loss_rate_factor = LossRateFactors.apc
                    recovery_rate = rr.apc
                    cr_total = cr.personnel * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.combat_air_support:
                    loss_rate_factor = LossRateFactors.fixed_wing
                    recovery_rate = rr.fixed_wing
                    cr_total = cr.personnel * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.fighter:
                    loss_rate_factor = LossRateFactors.fixed_wing
                    recovery_rate = rr.fixed_wing
                    cr_total = cr.personnel * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.bomber:
                    loss_rate_factor = LossRateFactors.fixed_wing
                    recovery_rate = rr.fixed_wing
                    cr_total = cr.personnel * loss_rate_factor
                elif e.qjm_vehicle_category == VehicleCategory.helicopter:
                    loss_rate_factor = LossRateFactors.rotary_wing
                    recovery_rate = rr.rotary_wing
                    cr_total = cr.personnel * loss_rate_factor
                else:
                    loss_rate_factor = LossRateFactors.infantry_weaps
                    recovery_rate = rr.infantry_weaps
                    cr_total = cr.personnel * loss_rate_factor
            else:
                # if still not found, log a warning
                logging.warning(f'{self} qjm equipment {e} not assigned a category! '\
                                f'Assigned equipment: {self.assigned_equipment}')
                loss_rate_factor = LossRateFactors.vehicles
                recovery_rate = rr.vehicles
                cr_total = cr.personnel * loss_rate_factor
            
            # test if the vehicle is hit
            if random() < cr_total:
                # vehicle is hit
                # test if it is destroyed
                if random() < recovery_rate:
                    # vehicle is damaged
                    self.status = ElementStatus.DAMAGED
                else:
                    # vehicle is destroyed
                    self.status = ElementStatus.DESTROYED
                
                # Add casualties to the crew of the destroyed vehicle
                for crew in self.crew:
                    crew.test_casualty(cr)
                
        return self.status
    
    def __repr__(self):
        return f"Vehicle({self.name})"