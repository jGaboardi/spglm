"""
Defines the link functions to be used with GLM and GEE families.
"""

import numpy as np
import scipy.stats

FLOAT_EPS = np.finfo(float).eps


class Link:
    """
    A generic link function for one-parameter exponential family.

    `Link` does nothing, but lays out the methods expected of any subclass.
    """

    def __call__(self, p):
        """
        Return the value of the link function.  This is just a placeholder.

        Parameters
        ----------
        p : array-like
            Probabilities

        Returns
        -------
        g(p) : array-like
            The value of the link function g(p) = z
        """
        return NotImplementedError

    def inverse(self, z):
        """
        Inverse of the link function.  Just a placeholder.

        Parameters
        ----------
        z : array-like
            `z` is usually the linear predictor of the transformed variable
            in the IRLS algorithm for GLM.

        Returns
        -------
        g^(-1)(z) : array
            The value of the inverse of the link function g^(-1)(z) = p


        """
        return NotImplementedError

    def deriv(self, p):
        """
        Derivative of the link function g'(p).  Just a placeholder.

        Parameters
        ----------
        p : array-like

        Returns
        -------
        g'(p) : array
            The value of the derivative of the link function g'(p)
        """
        return NotImplementedError

    def deriv2(self, p):
        """Second derivative of the link function g''(p)

        implemented through numerical differentiation
        """
        from statsmodels.tools.numdiff import approx_fprime_cs

        # TODO: workaround proplem with numdiff for 1d
        return np.diag(approx_fprime_cs(p, self.deriv))

    def inverse_deriv(self, z):
        """
        Derivative of the inverse link function g^(-1)(z).

        Notes
        -----
        This reference implementation gives the correct result but is
        inefficient, so it can be overriden in subclasses.

        Parameters
        ----------
        z : array-like
            `z` is usually the linear predictor for a GLM or GEE model.

        Returns
        -------
        g'^(-1)(z) : array
            The value of the derivative of the inverse of the link function

        """
        return 1 / self.deriv(self.inverse(z))


class Logit(Link):
    """
    The logit transform

    Notes
    -----
    call and derivative use a private method _clean to make trim p by
    machine epsilon so that p is in (0,1)

    Alias of Logit:
    logit = Logit()
    """

    def _clean(self, p):
        """
        Clip logistic values to range (eps, 1-eps)

        Parameters
        -----------
        p : array-like
            Probabilities

        Returns
        --------
        pclip : array
            Clipped probabilities
        """
        return np.clip(p, FLOAT_EPS, 1.0 - FLOAT_EPS)

    def __call__(self, p):
        """
        The logit transform

        Parameters
        ----------
        p : array-like
            Probabilities

        Returns
        -------
        z : array
            Logit transform of `p`

        Notes
        -----
        g(p) = log(p / (1 - p))
        """
        p = self._clean(p)
        return np.log(p / (1.0 - p))

    def inverse(self, z):
        """
        Inverse of the logit transform

        Parameters
        ----------
        z : array-like
            The value of the logit transform at `p`

        Returns
        -------
        p : array
            Probabilities

        Notes
        -----
        g^(-1)(z) = exp(z)/(1+exp(z))
        """
        z = np.asarray(z)
        t = np.exp(-z)
        return 1.0 / (1.0 + t)

    def deriv(self, p):
        """
        Derivative of the logit transform

        Parameters
        ----------
        p: array-like
            Probabilities

        Returns
        -------
        g'(p) : array
            Value of the derivative of logit transform at `p`

        Notes
        -----
        g'(p) = 1 / (p * (1 - p))

        Alias for `Logit`:
        logit = Logit()
        """
        p = self._clean(p)
        return 1.0 / (p * (1 - p))

    def inverse_deriv(self, z):
        """
        Derivative of the inverse of the logit transform

        Parameters
        ----------
        z : array-like
            `z` is usually the linear predictor for a GLM or GEE model.

        Returns
        -------
        g'^(-1)(z) : array
            The value of the derivative of the inverse of the logit function

        """
        t = np.exp(z)
        return t / (1 + t) ** 2

    def deriv2(self, p):
        """
        Second derivative of the logit function.

        Parameters
        ----------
        p : array-like
            probabilities

        Returns
        -------
        g''(z) : array
            The value of the second derivative of the logit function
        """
        v = p * (1 - p)
        return (2 * p - 1) / v**2


class logit(Logit):
    pass


class Power(Link):
    """
    The power transform

    Parameters
    ----------
    power : float
        The exponent of the power transform

    Notes
    -----
    Aliases of Power:
    inverse = Power(power=-1)
    sqrt = Power(power=.5)
    inverse_squared = Power(power=-2.)
    identity = Power(power=1.)
    """

    def __init__(self, power=1.0):
        self.power = power

    def __call__(self, p):
        """
        Power transform link function

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        z : array-like
            Power transform of x

        Notes
        -----
        g(p) = x**self.power
        """

        z = np.power(p, self.power)
        return z

    def inverse(self, z):
        """
        Inverse of the power transform link function

        Parameters
        ----------
        `z` : array-like
            Value of the transformed mean parameters at `p`

        Returns
        -------
        `p` : array
            Mean parameters

        Notes
        -----
        g^(-1)(z`) = `z`**(1/`power`)
        """

        p = np.power(z, 1.0 / self.power)
        return p

    def deriv(self, p):
        """
        Derivative of the power transform

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        --------
        g'(p) : array
            Derivative of power transform of `p`

        Notes
        -----
        g'(`p`) = `power` * `p`**(`power` - 1)
        """
        return self.power * np.power(p, self.power - 1)

    def deriv2(self, p):
        """
        Second derivative of the power transform

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        --------
        g''(p) : array
            Second derivative of the power transform of `p`

        Notes
        -----
        g''(`p`) = `power` * (`power` - 1) * `p`**(`power` - 2)
        """
        return self.power * (self.power - 1) * np.power(p, self.power - 2)

    def inverse_deriv(self, z):
        """
        Derivative of the inverse of the power transform

        Parameters
        ----------
        z : array-like
            `z` is usually the linear predictor for a GLM or GEE model.

        Returns
        -------
        g^(-1)'(z) : array
            The value of the derivative of the inverse of the power transform
        function
        """
        return np.power(z, (1 - self.power) / self.power) / self.power


class inverse_power(Power):
    """
    The inverse transform

    Notes
    -----
    g(p) = 1/p

    Alias of statsmodels.family.links.Power(power=-1.)
    """

    def __init__(self):
        super().__init__(power=-1.0)


class sqrt(Power):
    """
    The square-root transform

    Notes
    -----
    g(`p`) = sqrt(`p`)

    Alias of statsmodels.family.links.Power(power=.5)
    """

    def __init__(self):
        super().__init__(power=0.5)


class inverse_squared(Power):
    r"""
    The inverse squared transform

    Notes
    -----
    g(`p`) = 1/(`p`\ \*\*2)

    Alias of statsmodels.family.links.Power(power=2.)
    """

    def __init__(self):
        super().__init__(power=-2.0)


class identity(Power):
    """
    The identity transform

    Notes
    -----
    g(`p`) = `p`

    Alias of statsmodels.family.links.Power(power=1.)
    """

    def __init__(self):
        super().__init__(power=1.0)


class Log(Link):
    """
    The log transform

    Notes
    -----
    call and derivative call a private method _clean to trim the data by
    machine epsilon so that p is in (0,1). log is an alias of Log.
    """

    def _clean(self, x):
        return np.clip(x, FLOAT_EPS, np.inf)

    def __call__(self, p):
        """
        Log transform link function

        Parameters
        ----------
        x : array-like
            Mean parameters

        Returns
        -------
        z : array
            log(x)

        Notes
        -----
        g(p) = log(p)
        """
        x = self._clean(p)
        return np.log(x)

    def inverse(self, z):
        """
        Inverse of log transform link function

        Parameters
        ----------
        z : array
            The inverse of the link function at `p`

        Returns
        -------
        p : array
            The mean probabilities given the value of the inverse `z`

        Notes
        -----
        g^{-1}(z) = exp(z)
        """
        return np.exp(z)

    def deriv(self, p):
        """
        Derivative of log transform link function

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        g'(p) : array
            derivative of log transform of x

        Notes
        -----
        g'(x) = 1/x
        """
        p = self._clean(p)
        return 1.0 / p

    def deriv2(self, p):
        """
        Second derivative of the log transform link function

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        g''(p) : array
            Second derivative of log transform of x

        Notes
        -----
        g''(x) = -1/x^2
        """
        p = self._clean(p)
        return -1.0 / p**2

    def inverse_deriv(self, z):
        """
        Derivative of the inverse of the log transform link function

        Parameters
        ----------
        z : array
            The inverse of the link function at `p`

        Returns
        -------
        g^(-1)'(z) : array
            The value of the derivative of the inverse of the log function,
            the exponential function
        """
        return np.exp(z)


class log(Log):
    """
    The log transform

    Notes
    -----
    log is a an alias of Log.
    """

    pass


# TODO: the CDFLink is untested
class CDFLink(Logit):
    """
    The use the CDF of a scipy.stats distribution

    CDFLink is a subclass of logit in order to use its _clean method
    for the link and its derivative.

    Parameters
    ----------
    dbn : scipy.stats distribution
        Default is dbn=scipy.stats.norm

    Notes
    -----
    The CDF link is untested.
    """

    def __init__(self, dbn=scipy.stats.norm):
        self.dbn = dbn

    def __call__(self, p):
        """
        CDF link function

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        z : array
            (ppf) inverse of CDF transform of p

        Notes
        -----
        g(`p`) = `dbn`.ppf(`p`)
        """
        p = self._clean(p)
        return self.dbn.ppf(p)

    def inverse(self, z):
        """
        The inverse of the CDF link

        Parameters
        ----------
        z : array-like
            The value of the inverse of the link function at `p`

        Returns
        -------
        p : array
            Mean probabilities.  The value of the inverse of CDF link of `z`

        Notes
        -----
        g^(-1)(`z`) = `dbn`.cdf(`z`)
        """
        return self.dbn.cdf(z)

    def deriv(self, p):
        """
        Derivative of CDF link

        Parameters
        ----------
        p : array-like
            mean parameters

        Returns
        -------
        g'(p) : array
            The derivative of CDF transform at `p`

        Notes
        -----
        g'(`p`) = 1./ `dbn`.pdf(`dbn`.ppf(`p`))
        """
        p = self._clean(p)
        return 1.0 / self.dbn.pdf(self.dbn.ppf(p))

    def deriv2(self, p):
        """
        Second derivative of the link function g''(p)

        implemented through numerical differentiation
        """
        from statsmodels.tools.numdiff import approx_fprime

        p = np.atleast_1d(p)
        # Note: special function for norm.ppf does not support complex
        return np.diag(approx_fprime(p, self.deriv, centered=True))

    def inverse_deriv(self, z):
        """
        Derivative of the inverse of the CDF transformation link function

        Parameters
        ----------
        z : array
            The inverse of the link function at `p`

        Returns
        -------
        g^(-1)'(z) : array
            The value of the derivative of the inverse of the logit function
        """
        return 1 / self.deriv(self.inverse(z))


class probit(CDFLink):
    """
    The probit (standard normal CDF) transform

    Notes
    --------
    g(p) = scipy.stats.norm.ppf(p)

    probit is an alias of CDFLink.
    """

    pass


class cauchy(CDFLink):
    """
    The Cauchy (standard Cauchy CDF) transform

    Notes
    -----
    g(p) = scipy.stats.cauchy.ppf(p)

    cauchy is an alias of CDFLink with dbn=scipy.stats.cauchy
    """

    def __init__(self):
        super().__init__(dbn=scipy.stats.cauchy)

    def deriv2(self, p):
        """
        Second derivative of the Cauchy link function.

        Parameters
        ----------
        p: array-like
            Probabilities

        Returns
        -------
        g''(p) : array
            Value of the second derivative of Cauchy link function at `p`
        """
        a = np.pi * (p - 0.5)
        d2 = 2 * np.pi**2 * np.sin(a) / np.cos(a) ** 3
        return d2


class CLogLog(Logit):
    """
    The complementary log-log transform

    CLogLog inherits from Logit in order to have access to its _clean method
    for the link and its derivative.

    Notes
    -----
    CLogLog is untested.
    """

    def __call__(self, p):
        """
        C-Log-Log transform link function

        Parameters
        ----------
        p : array
            Mean parameters

        Returns
        -------
        z : array
            The CLogLog transform of `p`

        Notes
        -----
        g(p) = log(-log(1-p))
        """
        p = self._clean(p)
        return np.log(-np.log(1 - p))

    def inverse(self, z):
        """
        Inverse of C-Log-Log transform link function


        Parameters
        ----------
        z : array-like
            The value of the inverse of the CLogLog link function at `p`

        Returns
        -------
        p : array
            Mean parameters

        Notes
        -----
        g^(-1)(`z`) = 1-exp(-exp(`z`))
        """
        return 1 - np.exp(-np.exp(z))

    def deriv(self, p):
        """
        Derivative of C-Log-Log transform link function

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        g'(p) : array
            The derivative of the CLogLog transform link function

        Notes
        -----
        g'(p) = - 1 / ((p-1)*log(1-p))
        """
        p = self._clean(p)
        return 1.0 / ((p - 1) * (np.log(1 - p)))

    def deriv2(self, p):
        """
        Second derivative of the C-Log-Log ink function

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        g''(p) : array
            The second derivative of the CLogLog link function
        """
        p = self._clean(p)
        fl = np.log(1 - p)
        d2 = -1 / ((1 - p) ** 2 * fl)
        d2 *= 1 + 1 / fl
        return d2

    def inverse_deriv(self, z):
        """
        Derivative of the inverse of the C-Log-Log transform link function

        Parameters
        ----------
        z : array-like
            The value of the inverse of the CLogLog link function at `p`

        Returns
        -------
        g^(-1)'(z) : array
            The derivative of the inverse of the CLogLog link function
        """
        return np.exp(z - np.exp(z))


class cloglog(CLogLog):
    """
    The CLogLog transform link function.

    Notes
    -----
    g(`p`) = log(-log(1-`p`))

    cloglog is an alias for CLogLog
    cloglog = CLogLog()
    """

    pass


class NegativeBinomial:
    """
    The negative binomial link function

    Parameters
    ----------
    alpha : float, optional
        Alpha is the ancillary parameter of the Negative Binomial link
        function. It is assumed to be nonstochastic.  The default value is 1.
        Permissible values are usually assumed to be in (.01, 2).
    """

    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def _clean(self, x):
        return np.clip(x, FLOAT_EPS, np.inf)

    def __call__(self, p):
        """
        Negative Binomial transform link function

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        z : array
            The negative binomial transform of `p`

        Notes
        -----
        g(p) = log(p/(p + 1/alpha))
        """
        p = self._clean(p)
        return np.log(p / (p + 1 / self.alpha))

    def inverse(self, z):
        """
        Inverse of the negative binomial transform

        Parameters
        -----------
        z : array-like
            The value of the inverse of the negative binomial link at `p`.

        Returns
        -------
        p : array
            Mean parameters

        Notes
        -----
        g^(-1)(z) = exp(z)/(alpha*(1-exp(z)))
        """
        return -1 / (self.alpha * (1 - np.exp(-z)))

    def deriv(self, p):
        """
        Derivative of the negative binomial transform

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        g'(p) : array
            The derivative of the negative binomial transform link function

        Notes
        -----
        g'(x) = 1/(x+alpha*x^2)
        """
        return 1 / (p + self.alpha * p**2)

    def deriv2(self, p):
        """
        Second derivative of the negative binomial link function.

        Parameters
        ----------
        p : array-like
            Mean parameters

        Returns
        -------
        g''(p) : array
            The second derivative of the negative binomial transform link
            function

        Notes
        -----
        g''(x) = -(1+2*alpha*x)/(x+alpha*x^2)^2
        """
        numer = -(1 + 2 * self.alpha * p)
        denom = (p + self.alpha * p**2) ** 2
        return numer / denom

    def inverse_deriv(self, z):
        """
        Derivative of the inverse of the negative binomial transform

        Parameters
        -----------
        z : array-like
            Usually the linear predictor for a GLM or GEE model

        Returns
        -------
        g^(-1)'(z) : array
            The value of the derivative of the inverse of the negative
            binomial link
        """
        t = np.exp(z)
        return t / (self.alpha * (1 - t) ** 2)


class nbinom(NegativeBinomial):
    """
    The negative binomial link function.

    Notes
    -----
    g(p) = log(p/(p + 1/alpha))

    nbinom is an alias of NegativeBinomial.
    nbinom = NegativeBinomial(alpha=1.)
    """

    pass
