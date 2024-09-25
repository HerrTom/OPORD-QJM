

class LIN:
    def __init__(self, lin: str, name: str, items: list):
        """
        Initialize a new LIN (Line Item Number).

        Args:
            lin (str): The Line Item Number.
            name (str): The name of the LIN.
            items (list): A list of item entries associated with the LIN.
        """
        self.lin = lin
        self.name = name
        self.item_entries = items

    def assign_equipment(self, nsns: list):
        """_summary_

        Args:
            nsns (list): List of available NSNs to choose from. If none of the NSNs
                in this list are available to this LIN, it will return the highest priority item.
                TODO: Should this return the *lowest* priority instead?

        Returns:
            str: Accepted NSN of given equipment
        """
        available = []
        for nsn in nsns:
            if nsn in self.item_entries:
                available.append(nsn)
        # For now, we will choose the first found NSN. TODO: do actual sorting for highest priority
        if len(available) > 0:
            equipment = available[0]
        else:
            equipment = self.item_entries[0]

        return equipment

    def __repr__(self,):
        return 'LIN {} ({})'.format(self.lin, self.name)
