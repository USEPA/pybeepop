"""BeePop+ Colony Resource Management Module.

This module contains classes for managing colony food resources including pollen
and nectar stores with associated pesticide contamination tracking.

Classes:
    ResourceItem: Individual resource unit with contamination tracking
    ColonyResource: Colony-level resource stores with pesticide management
"""


class ResourceItem:
    """Individual resource unit with associated pesticide contamination.

    Represents a discrete quantity of colony resource (pollen or nectar) with
    its associated pesticide load. Used for tracking contamination levels and
    implementing resource-based mortality and sublethal effects.

    Attributes:
        resource_quantity (float): Amount of resource (grams)
        pesticide_quantity (float): Associated pesticide load (grams)
    """

    def __init__(self, resource_quantity=0.0, pesticide_quantity=0.0):
        self.resource_quantity = resource_quantity
        self.pesticide_quantity = pesticide_quantity


class ColonyResource:
    """Colony-level resource management with pollen and nectar stores.

    Manages colony food resources including pollen and nectar quantities with
    associated pesticide contamination tracking. Provides resource consumption,
    storage limits, and contamination concentration calculations for colony
    survival and brood rearing dynamics.

    Resources support larval development, adult maintenance, and colony growth.
    Pesticide contamination affects bee mortality and reproductive success.
    Resource depletion can trigger colony decline or collapse scenarios.

    Attributes:
        pollen_quantity (float): Current pollen stores in grams
        nectar_quantity (float): Current nectar stores in grams
        pollen_pesticide_quantity (float): Total pesticide load in pollen stores in grams
        nectar_pesticide_quantity (float): Total pesticide load in nectar stores in grams
    """

    def __init__(self):
        self.pollen_quantity = 0.0
        self.nectar_quantity = 0.0
        self.pollen_pesticide_quantity = 0.0
        self.nectar_pesticide_quantity = 0.0

    # Gets and Sets
    def get_pollen_quantity(self):
        return self.pollen_quantity

    def get_nectar_quantity(self):
        return self.nectar_quantity

    def get_pollen_pesticide_quantity(self):
        return self.pollen_pesticide_quantity

    def get_nectar_pesticide_quantity(self):
        return self.nectar_pesticide_quantity

    def get_pollen_pesticide_concentration(self):
        if self.pollen_quantity > 0:
            return self.pollen_pesticide_quantity / self.pollen_quantity
        return 0.0

    def get_nectar_pesticide_concentration(self):
        if self.nectar_quantity > 0:
            return self.nectar_pesticide_quantity / self.nectar_quantity
        return 0.0

    def set_pollen_quantity(self, quan):
        self.pollen_quantity = quan

    def set_nectar_quantity(self, quan):
        self.nectar_quantity = quan

    def set_pollen_pesticide_quantity(self, quan):
        self.pollen_pesticide_quantity = quan

    def set_nectar_pesticide_quantity(self, quan):
        self.nectar_pesticide_quantity = quan

    # Methods
    def initialize(self, init_pollen=0.0, init_nectar=0.0):
        self.pollen_quantity = init_pollen
        self.nectar_quantity = init_nectar
        self.pollen_pesticide_quantity = 0.0
        self.nectar_pesticide_quantity = 0.0

    def add_pollen(self, pollen: ResourceItem):
        self.pollen_quantity += pollen.resource_quantity
        self.pollen_pesticide_quantity += pollen.pesticide_quantity

    def add_nectar(self, nectar: ResourceItem):
        self.nectar_quantity += nectar.resource_quantity
        self.nectar_pesticide_quantity += nectar.pesticide_quantity

    def remove_pollen(self, amount):
        """Remove pollen - matches C++ RemovePollen(double Amount)"""
        # Pollen cannot go below zero
        if self.pollen_quantity >= amount:
            self.pollen_quantity -= amount
            self.pollen_pesticide_quantity -= (
                amount * self.get_pollen_pesticide_concentration()
            )
            if self.pollen_pesticide_quantity < 0:
                self.pollen_pesticide_quantity = 0
        else:
            self.pollen_quantity = 0.0
            self.pollen_pesticide_quantity = 0.0

    def remove_pollen_with_return(self, amount, pollen: ResourceItem):
        """Remove pollen and return removed amount - matches C++ RemovePollen(double Amount, SResourceItem &Pollen)"""
        if self.pollen_quantity >= amount:
            # Pollen
            pollen.resource_quantity = amount
            self.pollen_quantity -= amount
            if self.pollen_quantity < 0:
                self.pollen_quantity = 0

            # Pesticide
            pollen.pesticide_quantity = (
                self.get_pollen_pesticide_concentration() * pollen.resource_quantity
            )
            self.pollen_pesticide_quantity -= pollen.pesticide_quantity
            if self.pollen_pesticide_quantity < 0:
                self.pollen_pesticide_quantity = 0
        else:
            pollen.resource_quantity = self.pollen_quantity
            pollen.pesticide_quantity = self.pollen_pesticide_quantity
            self.pollen_quantity = 0.0
            self.pollen_pesticide_quantity = 0.0

    def remove_nectar(self, amount):
        """Remove nectar - matches C++ RemoveNectar(double Amount)"""
        # Nectar cannot go below zero
        if self.nectar_quantity >= amount:
            self.nectar_quantity -= amount
            self.nectar_pesticide_quantity -= (
                amount * self.get_nectar_pesticide_concentration()
            )
            if self.nectar_pesticide_quantity < 0:
                self.nectar_pesticide_quantity = 0
        else:
            self.nectar_quantity = 0.0
            self.nectar_pesticide_quantity = 0.0

    def remove_nectar_with_return(self, amount, nectar: ResourceItem):
        """Remove nectar and return removed amount - matches C++ RemoveNectar(double Amount, SResourceItem &Nectar)"""
        if self.nectar_quantity >= amount:
            # Nectar
            nectar.resource_quantity = amount
            self.nectar_quantity -= amount
            if self.nectar_quantity < 0:
                self.nectar_quantity = 0

            # Pesticide
            nectar.pesticide_quantity = (
                self.get_nectar_pesticide_concentration() * nectar.resource_quantity
            )
            self.nectar_pesticide_quantity -= nectar.pesticide_quantity
            if self.nectar_pesticide_quantity < 0:
                self.nectar_pesticide_quantity = 0
        else:
            nectar.resource_quantity = self.nectar_quantity
            nectar.pesticide_quantity = self.nectar_pesticide_quantity
            self.nectar_quantity = 0.0
            self.nectar_pesticide_quantity = 0.0
