# Helper function to generate a SIDC code

class SIDC:
    def __init__(self,):
        # Set A. The first set of ten digits:
        #     Digits 1 and 2 is the Version.
        self.version = '10'
        #     Digits 3 and 4 is the Standard Identity.
        self.standard_identity_context = '0' # reality
        self.standard_identity  = '3' # friendly
        #     Digits 5 and 6 is the Symbol Set.
        self.symbol_set = '10'
        #     Digit 7 is the Status.
        self.status = '0' # present
        #     Digit 8 is the Headquarters/Task Force/Dummy.
        self.headquarters = '0'
        #     Digits 9 and 10 is the Amplifier/Descriptor.
        self.echelon_amplifier = '17' # Regiment
        # Set B. The second set of ten digits:
        #     Digits 11 and 12 is the entity.
        self.entity = '12' # Movement and Maneuver
        #     Digits 13 and 14 is the entity type.
        self.entity_type = '05' # Armor
        #     Digits 15 and 16 is the entity subtype.
        self.entity_subtype = '01' # Reconnaissance/Cavalry/Scout
        #     Digits 17 and 18 is the first modifier.
        self.first_modifier = '00'
        #     Digits 19 and 20 is the second modifier.
        self.second_modifier = '00'

        self.sidc = ''.join([self.version, self.standard_identity_context, self.standard_identity,
                              self.symbol_set, self.status, self.headquarters,
                              self.echelon_amplifier, self.entity, self.entity_type,
                              self.entity_subtype, self.first_modifier, self.second_modifier])
        

s = SIDC()

print(s.sidc)