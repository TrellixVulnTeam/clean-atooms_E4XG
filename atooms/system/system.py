# This file is part of atooms
# Copyright 2010-2014, Daniele Coslovich

"""
The physical system at hand.

The systems of interest in classical atomistic simulations are made of
interacting point particles, usually enclosed in a simulation
cell. The system may be in contact with a thermostat, a barostat or a
particle reservoir.
"""

import numpy
from .particle import cm_position, cm_velocity, fix_total_momentum


class System(object):

    """System class."""

    def __init__(self, particle=None, cell=None, interaction=None,
                 thermostat=None, barostat=None, reservoir=None):
        if particle is None:
            particle = []
        self.particle = particle
        """A list of `Particle` instances."""
        self.interaction = interaction
        self.cell = cell
        self.thermostat = thermostat
        self.barostat = barostat
        self.reservoir = reservoir
        self.matrix = None

    @property
    def number_of_dimensions(self):
        """
        Number of spatial dimensions, guessed from the length of
        `particle[0].position`.
        """
        return len(self.particle[0].position)

    def distinct_species(self):
        """Sorted list of distinct chemical species in the system."""
        return sorted(set(p.species for p in self.particle))

    @property
    def density(self):
        """
        Density of the system.

        It will raise a ValueException if `cell` is None.
        """
        if self.cell is None:
            return ValueError('cannot compute density without a cell')
        return len(self.particle) / self.cell.volume

    @density.setter
    def density(self, rho):
        self.set_density(rho)

    def set_density(self, rho):
        """Set the system density to `rho` by rescaling the coordinates."""
        if self.cell is None:
            return ValueError('cannot compute density without a cell')
        factor = (self.density / rho)**(1./3)
        for particle in self.particle:
            particle.position *= factor
        self.cell.side *= factor

    @property
    def packing_fraction(self):
        from math import pi
        return pi / 6 * sum([(2 * p.radius)**3 for p in self.particle]) / self.cell.volume

    @property
    def temperature(self):
        """
        Kinetic temperature.

        If given, `ndof` specifies the number of degrees of freedom to
        correct for missing translational invariance. Otherwise,

            ndof = (N-1)*dim
        """
        # TODO: determine translational invariance via some additional attribute.
        ndof = (len(self.particle)-1) * self.number_of_dimensions
        return 2.0 / ndof * self.kinetic_energy()

    @temperature.setter
    def temperature(self, T):
        self.set_temperature(T)

    def set_temperature(self, temperature):
        """Reset velocities to a Maxwellian distribution with fixed CM."""
        T = temperature
        for p in self.particle:
            p.maxwellian(T)
        fix_total_momentum(self.particle)
        # After fixing the CM the temperature is not exactly the targeted one
        # Therefore we scale the velocities so as to get to the right T
        T_old = self.temperature
        fac = (T/T_old)**0.5
        for p in self.particle:
            p.velocity *= fac

    def kinetic_energy(self, normed=False):
        """
        Return the total kinetic energy of the system.

        If `normed` is `True`, return the kinetic energy per
        particle.
        """
        ekin = sum([p.kinetic_energy for p in self.particle])
        if not normed:
            return ekin
        else:
            return ekin / len(self.particle)

    def potential_energy(self, normed=False):
        """
        Return the total potential energy of the system.

        If `normed` is `True`, return the potential energy per
        particle.
        """
        if self.interaction is not None:
            self.interaction.compute('energy', self.particle, self.cell)
            if not normed:
                return self.interaction.energy
            else:
                return self.interaction.energy / len(self.particle)
        else:
            return 0.0

    def total_energy(self, normed=False):
        """
        Return the total energy of the system.

        If `normed` is `True`, return the total energy per particle.
        """
        return self.potential_energy(normed) + self.kinetic_energy(normed)

    @property
    def cm_velocity(self):
        """Center-of-mass velocity."""
        return cm_velocity(self.particle)

    @property
    def cm_position(self):
        """Center-of-mass position."""
        return cm_position(self.particle)

    def fix_momentum(self):
        """Subtract out the the center-of-mass motion."""
        fix_total_momentum(self.particle)

    def mean_square_displacement(self, other):
        """
        Return the mean square displacement of the system's particles with
        respect to those of an `other` System instance.
        """
        displ = []
        for pi, pj in zip(self.particle, other.particle):
            rij = pi.distance(pj, folded=False)
            displ.append(numpy.dot(rij, rij))
        return sum(displ) / len(self.particle)

    def dump(self, what, order='C', dtype=None):
        """
        Return a numpy array with system properties specified by `what`.

        If `what` is a string, it should be of the form
        `particle.<attribute>` or `cell.<attribute>`. The following
        aliases are allowed: pos, vel, ids, box.

        If `what` is a list of strings of the form above, a dict of
        numpy arrays is returned with `what` as keys.

        Particles' coordinates are retruned as (N, ndim) arrays if
        `order` is `C` or (ndim, N) arrays if `order` is `F`.

        Examples:
        --------
        These two numpy arrays are element-wise identical

            #!python
            pos = system.dump('particle.position')
            pos = system.dump('pos')

        Return a dict with both positions and velocities

            #!python
            dump = system.dump(['pos', 'vel'])
        """
        # Listify input variables
        if type(what) is str:
            what_list = [what]
            dtype_list = [dtype]
        else:
            what_list = what
            if dtype is None:
                dtype_list = [None] * len(what_list)

        aliases = {'pos': 'particle.position',
                   'vel': 'particle.velocity',
                   'spe': 'particle.species'}

        dump_db = {}
        for what, dtype in zip(what_list, dtype_list):
            # Accept some aliases
            if what in aliases:
                what_aliased = aliases[what]
            else:
                what_aliased = what
            # Extract the requested attribute
            attr = what_aliased.split('.')[-1]
            # Make array of attributes
            if what_aliased.startswith('particle'):
                data = numpy.array([p.__getattribute__(attr) for p in self.particle], dtype=dtype)
            else:
                raise ValueError('Unknown attribute %s' % what_aliased)
            # We transpose the array if F order is requested (only meaningful for 2d arrays)
            if order == 'F':
                data = numpy.transpose(data)
            dump_db[what] = data

        # If what is a string or we only have one entry we return an
        # array, otherwise we return the whole dict
        if len(what_list) == 1:
            return dump_db.values()[0]
        else:
            return dump_db
