"""2D Vector Class

Based on https://scipython.com/book2/chapter-4-the-core-python-language-ii/examples/a-2d-vector-class/
"""
import math

class Vector2D:
    """A two-dimensional vector with Cartesian coordinates."""

    def __init__(self, x, y):
        self.x, self.y = x, y

    def __str__(self):
        """Human-readable string representation of the vector."""
        return repr((round(self.x,4), round(self.y,4)))
        # return '{:g}i + {:g}j'.format(self.x, self.y)

    def __repr__(self):
        """Unambiguous string representation of the vector."""
        return repr((self.x, self.y))

    def dot(self, other):
        """The scalar (dot) product of self and other. Both must be vectors."""

        if not isinstance(other, Vector2D):
            raise TypeError('Can only take dot product of two Vector2D objects')
        return self.x * other.x + self.y * other.y
    # Alias the __matmul__ method to dot so we can use a @ b as well as a.dot(b).
    __matmul__ = dot

    def __sub__(self, other):
        """Vector subtraction."""
        return Vector2D(self.x - other.x, self.y - other.y)

    def __add__(self, other):
        """Vector addition."""
        return Vector2D(self.x + other.x, self.y + other.y)

    def __mul__(self, scalar):
        """Multiplication of a vector by a scalar."""

        if isinstance(scalar, int) or isinstance(scalar, float):
            return Vector2D(self.x*scalar, self.y*scalar)
        raise NotImplementedError('Can only multiply Vector2D by a scalar')

    def __rmul__(self, scalar):
        """Reflected multiplication so vector * scalar also works."""
        return self.__mul__(scalar)

    def __neg__(self):
        """Negation of the vector (invert through origin.)"""
        return Vector2D(-self.x, -self.y)

    def __truediv__(self, scalar):
        """True division of the vector by a scalar."""
        return Vector2D(self.x / scalar, self.y / scalar)

    def __mod__(self, scalar):
        """One way to implement modulus operation: for each component."""
        return Vector2D(self.x % scalar, self.y % scalar)

    def __abs__(self):
        """Absolute value (magnitude) of the vector. i.e. ||self|| """
        return math.sqrt(self.x**2 + self.y**2)

    def distance_to(self, other):
        """The distance between vectors self and other."""
        return abs(self - other)

    def to_polar(self):
        """Return the vector's components in polar coordinates."""
        return self.__abs__(), math.atan2(self.y, self.x)

    def project(self, other):
        """Return a vector that is the vector projected onto other.

        https://matthew-brett.github.io/teaching/vector_projection.html
        """
        return ((self @ other)/abs(other)**2)*other

    def unit(self):
        """Return a unit vector of the vector."""
        return self / abs(self)

    def ortho(self):
        """Return a vector that is orthogonal."""
        return Vector2D(self.y, -self.x)

    def reflect(self, other):
        """Return a vector that is reflected off other

        https://bluebill.net/vector_reflection.html
        """
        normal = other.ortho().unit()
        return self - 2 * (self @ normal) * normal


if __name__ == '__main__':
    #v1 = Vector2D(2, 5/3)
    #v2 = Vector2D(3, -1.5)

    #v1 = Vector2D(0, 1)
    #v2 = Vector2D(0, 1)

    v1 = Vector2D(10, 10)
    v2 = Vector2D(1, 2)

    print('v1 = ', v1)
    print('repr(v2) = ', repr(v2))
    print('v1 + v2 = ', v1 + v2)
    print('v1 - v2 = ', v1 - v2)
    print('abs(v2 - v1) = ', abs(v2 - v1))
    print('-v2 = ', -v2)
    print('v1 * 3 = ', v1 * 3)
    print('7 * v2 = ', 7 * v1)
    print('v2 / 2.5 = ', v2 / 2.5)
    print('v1 % 1 = ', v1 % 1)
    print('v1.dot(v2) = v1 @ v2 = ', v1 @ v2)
    print('v1.distance_to(v2) = ',v1.distance_to(v2))
    print('v1 as polar vector, (r, theta) =', v1.to_polar())
    print('v1 project onto v2 = ', v1.project(v2))
    print('v2 project onto v1 = ', v2.project(v1))
    print('v1 unit vector = ', v1.unit())
    print('v2 unit vector = ', v2.unit())
    print('v1 ortho vector = ', v1.ortho())
    print('v2 ortho vector = ', v2.ortho())
    print('v1 refect off v2 = ', v1.reflect(v2))