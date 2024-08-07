"""
The one parameter exponential family distributions used by GLM.
"""

# TODO: quasi, quasibinomial, quasipoisson
# see http://www.biostat.jhsph.edu/~qli/biostatistics_r_doc/library/stats/html/family.html
# for comparison to R, and McCullagh and Nelder

import numpy as np
from scipy import special

from . import links as L  # noqa: N812 - Lowercase imported as non-lowercase
from . import varfuncs as V  # noqa: N812

FLOAT_EPS = np.finfo(float).eps


class Family:
    """
    The parent class for one-parameter exponential families.

    Parameters
    ----------
    link : a link function instance
        Link is the linear transformation function.
        See the individual families for available links.
    variance : a variance function
        Measures the variance as a function of the mean probabilities.
        See the individual families for the default variance function.

    See Also
    --------
    :ref:`links`

    """

    # TODO: change these class attributes, use valid somewhere...
    valid = [-np.inf, np.inf]

    links = []

    def _setlink(self, link):
        """
        Helper method to set the link for a family.

        Raises a ValueError exception if the link is not available.  Note that
        the error message might not be that informative because it tells you
        that the link should be in the base class for the link function.

        See glm.GLM for a list of appropriate links for each family but note
        that not all of these are currently available.
        """
        # TODO: change the links class attribute in the families to hold
        # meaningful information instead of a list of links instances such as
        # [<statsmodels.family.links.Log object at 0x9a4240c>,
        #  <statsmodels.family.links.Power object at 0x9a423ec>,
        #  <statsmodels.family.links.Power object at 0x9a4236c>]
        # for Poisson...
        self._link = link
        if not isinstance(link, L.Link):
            raise TypeError("The input should be a valid Link object.")
        if hasattr(self, "links"):
            validlink = link in self.links
            validlink = max([isinstance(link, _) for _ in self.links])
            if not validlink:
                errmsg = "Invalid link for family, should be in %s. (got %s)"
                raise ValueError(errmsg % (repr(self.links), link))

    def _getlink(self):
        """
        Helper method to get the link for a family.
        """
        return self._link

    # link property for each family is a pointer to link instance
    link = property(_getlink, _setlink, doc="Link function for family")

    def __init__(self, link, variance):
        self.link = link()
        self.variance = variance

    def starting_mu(self, y):
        r"""
        Starting value for mu in the IRLS algorithm.

        Parameters
        ----------
        y : array
            The untransformed response variable.

        Returns
        -------
        mu_0 : array
            The first guess on the transformed response variable.

        """
        return (y + y.mean()) / 2.0

    def weights(self, mu):
        r"""
        Weights for IRLS steps

        Parameters
        ----------
        mu : array-like
            The transformed mean response variable in the exponential family

        Returns
        -------
        w : array
            The weights for the IRLS steps

        """
        return 1.0 / (self.link.deriv(mu) ** 2 * self.variance(mu))

    def deviance(self, endog, mu, freq_weights=1.0, scale=1.0):
        r"""
        The deviance function evaluated at (endog,mu,freq_weights,mu).

        Deviance is usually defined as twice the loglikelihood ratio.

        Parameters
        ----------
        endog : array-like
            The endogenous response variable
        mu : array-like
            The inverse of the link function at the linear predicted values.
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            An optional scale argument. The default is 1.

        Returns
        -------
        Deviance : array
            The value of deviance function defined below.

        """
        raise NotImplementedError

    def resid_dev(self, endog, mu, freq_weights=1.0, scale=1.0):
        """
        The deviance residuals

        Parameters
        ----------
        endog : array
            The endogenous response variable
        mu : array
            The inverse of the link function at the linear predicted values.
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            An optional argument to divide the residuals by scale. The default
            is 1.

        Returns
        -------
        Deviance residuals.

        """
        raise NotImplementedError

    def fitted(self, lin_pred):
        """
        Fitted values based on linear predictors lin_pred.

        Parameters
        -----------
        lin_pred : array
            Values of the linear predictor of the model.
            dot(X,beta) in a classical linear model.

        Returns
        --------
        mu : array
            The mean response variables given by the inverse of the link
            function.
        """
        fits = self.link.inverse(lin_pred)
        return fits

    def predict(self, mu):
        """
        Linear predictors based on given mu values.

        Parameters
        ----------
        mu : array
            The mean response variables

        Returns
        -------
        lin_pred : array
            Linear predictors based on the mean response variables.  The value
            of the link function at the given mu.
        """
        return self.link(mu)

    def loglike(self, endog, mu, freq_weights=1.0, scale=1.0):
        """
        The log-likelihood function in terms of the fitted mean response.

        Parameters
        ----------
        `endog` : array
            Usually the endogenous response variable.
        `mu` : array
            Usually but not always the fitted mean response variable.
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float
            The scale parameter. The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood evaluated at
            (endog,mu,freq_weights,scale) as defined below.
        """
        raise NotImplementedError

    def resid_anscombe(self, endog, mu):
        """
        The Anscome residuals.

        See also
        --------
        statsmodels.families.family.Family docstring and the `resid_anscombe`
        for the individual families for more information.
        """
        raise NotImplementedError


class Poisson(Family):
    """
    Poisson exponential family.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Poisson family is the log link. Available
        links are log, identity, and sqrt. See statsmodels.family.links for
        more information.

    Attributes
    ----------
    Poisson.link : a link instance
        The link function of the Poisson instance.
    Poisson.variance : varfuncs instance

    """

    links = [L.log, L.identity, L.sqrt]
    variance = V.mu
    valid = [0, np.inf]
    safe_links = [
        L.Log,
    ]

    def __init__(self, link=L.log):
        self.variance = Poisson.variance
        self.link = link()

    def _clean(self, x):
        """
        Helper function to trim the data so that is in (0,inf)

        """
        return np.clip(x, FLOAT_EPS, np.inf)

    def resid_dev(self, endog, mu, scale=1.0):
        r"""Poisson deviance residual

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            An optional argument to divide the residuals by scale. The default
            is 1.

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        """
        endog_mu = self._clean(endog / mu)
        return (
            np.sign(endog - mu)
            * np.sqrt(2 * (endog * np.log(endog_mu) - (endog - mu)))
            / scale
        )

    def deviance(self, endog, mu, freq_weights=1.0, scale=1.0):
        r"""
        Poisson deviance function

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            An optional scale argument. The default is 1.

        Returns
        -------
        deviance : float
            The deviance function at (endog,mu,freq_weights,scale) as defined
            below.

        """
        endog_mu = self._clean(endog / mu)
        return 2 * np.sum(endog * freq_weights * np.log(endog_mu)) / scale

    def loglike(self, endog, mu, freq_weights=1.0, scale=1.0):
        r"""
        The log-likelihood function in terms of the fitted mean response.

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            The scale parameter, defaults to 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at
            (endog,mu,freq_weights,scale) as defined below.

        """
        loglike = np.sum(
            freq_weights * (endog * np.log(mu) - mu - special.gammaln(endog + 1))
        )
        return scale * loglike

    def resid_anscombe(self, endog, mu):
        r"""
        Anscombe residuals for the Poisson exponential family distribution

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscome residuals for the Poisson family defined below

        """
        return (3 / 2.0) * (endog ** (2 / 3.0) - mu ** (2 / 3.0)) / mu ** (1 / 6.0)


class QuasiPoisson(Family):
    """
    QuasiPoisson exponential family.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Poisson family is the log link. Available
        links are log, identity, and sqrt. See statsmodels.family.links for
        more information.

    Attributes
    ----------
    Poisson.link : a link instance
        The link function of the Poisson instance.
    Poisson.variance : varfuncs instance

    """

    links = [L.log, L.identity, L.sqrt]
    variance = V.mu
    valid = [0, np.inf]
    safe_links = [
        L.Log,
    ]

    def __init__(self, link=L.log):
        self.variance = Poisson.variance
        self.link = link()

    def _clean(self, x):
        """
        Helper function to trim the data so that is in (0,inf)

        """
        return np.clip(x, FLOAT_EPS, np.inf)

    def resid_dev(self, endog, mu, scale=1.0):
        r"""Poisson deviance residual

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            An optional argument to divide the residuals by scale. The default
            is 1.

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        """
        endog_mu = self._clean(endog / mu)
        return (
            np.sign(endog - mu)
            * np.sqrt(2 * (endog * np.log(endog_mu) - (endog - mu)))
            / scale
        )

    def deviance(self, endog, mu, freq_weights=1.0, scale=1.0):
        r"""
        Poisson deviance function

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            An optional scale argument. The default is 1.

        Returns
        -------
        deviance : float
            The deviance function at (endog,mu,freq_weights,scale) as defined
            below.

        """
        endog_mu = self._clean(endog / mu)
        return 2 * np.sum(endog * freq_weights * np.log(endog_mu)) / scale

    def loglike(self, endog, mu, freq_weights=1.0, scale=1.0):
        r"""
        The log-likelihood function in terms of the fitted mean response.

        Returns NaN for QuasiPoisson

        Returns
        -------
        None: not applicable for QuasiPoisson
        """
        return np.nan

    def resid_anscombe(self, endog, mu):
        r"""
        Anscombe residuals for the Poisson exponential family distribution

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscome residuals for the Poisson family defined below

        """
        return (3 / 2.0) * (endog ** (2 / 3.0) - mu ** (2 / 3.0)) / mu ** (1 / 6.0)


class Gaussian(Family):
    """
    Gaussian exponential family distribution.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Gaussian family is the identity link.
        Available links are log, identity, and inverse.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    Gaussian.link : a link instance
        The link function of the Gaussian instance
    Gaussian.variance : varfunc instance
    """

    links = [L.log, L.identity, L.inverse_power]
    variance = V.constant
    safe_links = links

    def __init__(self, link=L.identity):
        self.variance = Gaussian.variance
        self.link = link()

    def resid_dev(self, endog, mu, scale=1.0):
        """
        Gaussian deviance residuals

        Parameters
        -----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            An optional argument to divide the residuals by scale. The default
            is 1.

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        """

        return (endog - mu) / np.sqrt(self.variance(mu)) / scale

    def deviance(self, endog, mu, freq_weights=1.0, scale=1.0):
        """
        Gaussian deviance function

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            An optional scale argument. The default is 1.

        Returns
        -------
        deviance : float
            The deviance function at (endog,mu,freq_weights,scale)
            as defined below.

        """
        return np.sum(freq_weights * (endog - mu) ** 2) / scale

    def loglike(self, endog, mu, freq_weights=1.0, scale=1.0):
        """
        The log-likelihood in terms of the fitted mean response.

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            Scales the loglikelihood function. The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at
            (endog,mu,freq_weights,scale) as defined below.

        """
        if isinstance(self.link, L.Power) and self.link.power == 1:
            # This is just the loglikelihood for classical OLS
            nobs2 = endog.shape[0] / 2.0
            SSR = np.sum((endog - self.fitted(mu)) ** 2, axis=0)
            llf = -np.log(SSR) * nobs2
            llf -= (1 + np.log(np.pi / nobs2)) * nobs2
            return llf
        else:
            return np.sum(
                freq_weights
                * (
                    (endog * mu - mu**2 / 2) / scale
                    - endog**2 / (2 * scale)
                    - 0.5 * np.log(2 * np.pi * scale)
                )
            )

    def resid_anscombe(self, endog, mu):
        """
        The Anscombe residuals for the Gaussian exponential family distribution

        Parameters
        ----------
        endog : array
            Endogenous response variable
        mu : array
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals for the Gaussian family defined below

        """
        return endog - mu


class Gamma(Family):
    """
    Gamma exponential family distribution.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Gamma family is the inverse link.
        Available links are log, identity, and inverse.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    Gamma.link : a link instance
        The link function of the Gamma instance
    Gamma.variance : varfunc instance
    """

    links = [L.log, L.identity, L.inverse_power]
    variance = V.mu_squared
    safe_links = [
        L.Log,
    ]

    def __init__(self, link=L.inverse_power):
        self.variance = Gamma.variance
        self.link = link()

    def _clean(self, x):
        """
        Helper function to trim the data so that is in (0,inf)

        """
        return np.clip(x, FLOAT_EPS, np.inf)

    def deviance(self, endog, mu, freq_weights=1.0, scale=1.0):
        r"""
        Gamma deviance function

        Parameters
        -----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            An optional scale argument. The default is 1.

        Returns
        -------
        deviance : float
            Deviance function as defined below

        """
        endog_mu = self._clean(endog / mu)
        return 2 * np.sum(freq_weights * ((endog - mu) / mu - np.log(endog_mu)))

    def resid_dev(self, endog, mu, scale=1.0):
        r"""
        Gamma deviance residuals

        Parameters
        -----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            An optional argument to divide the residuals by scale. The default
            is 1.

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        """
        endog_mu = self._clean(endog / mu)
        return np.sign(endog - mu) * np.sqrt(
            -2 * (-(endog - mu) / mu + np.log(endog_mu))
        )

    def loglike(self, endog, mu, freq_weights=1.0, scale=1.0):
        r"""
        The log-likelihood function in terms of the fitted mean response.

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            The default is 1.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at
            (endog,mu,freq_weights,scale) as defined below.

        """
        return (
            -1.0
            / scale
            * np.sum(
                (
                    endog / mu
                    + np.log(mu)
                    + (scale - 1) * np.log(endog)
                    + np.log(scale)
                    + scale * special.gammaln(1.0 / scale)
                )
                * freq_weights
            )
        )

        # in Stata scale is set to equal 1 for reporting llf
        # in R it's the dispersion, though there is a loss of precision vs.
        # our results due to an assumed difference in implementation

    def resid_anscombe(self, endog, mu):
        r"""
        The Anscombe residuals for Gamma exponential family distribution

        Parameters
        ----------
        endog : array
            Endogenous response variable
        mu : array
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals for the Gamma family defined below

        """
        return 3 * (endog ** (1 / 3.0) - mu ** (1 / 3.0)) / mu ** (1 / 3.0)


class Binomial(Family):
    """
    Binomial exponential family distribution.

    Parameters
    ----------
    link : a link instance, optional
        The default link for the Binomial family is the logit link.
        Available links are logit, probit, cauchy, log, and cloglog.
        See statsmodels.family.links for more information.

    Attributes
    ----------
    Binomial.link : a link instance
        The link function of the Binomial instance
    Binomial.variance : varfunc instance

    """

    links = [L.logit, L.probit, L.cauchy, L.log, L.cloglog, L.identity]
    variance = V.binary  # this is not used below in an effort to include n

    # Other safe links, e.g. cloglog and probit are subclasses
    safe_links = [L.Logit, L.CDFLink]

    def __init__(self, link=L.logit):  # , n=1.):
        # TODO: it *should* work for a constant n>1 actually, if freq_weights
        # is equal to n
        self.n = 1
        # overwritten by initialize if needed but always used to initialize
        # variance since endog is assumed/forced to be (0,1)
        self.variance = V.Binomial(n=self.n)
        self.link = link()

    def starting_mu(self, y):
        r"""
        The starting values for the IRLS algorithm for the Binomial family.
        A good choice for the binomial family is :math:`\mu_0 = (Y_i + 0.5)/2`
        """
        return (y + 0.5) / 2

    def initialize(self, endog, freq_weights):
        """
        Initialize the response variable.

        Parameters
        ----------
        endog : array
            Endogenous response variable

        Returns
        --------
        If `endog` is binary, returns `endog`

        If `endog` is a 2d array, then the input is assumed to be in the format
        (successes, failures) and
        successes/(success + failures) is returned.  And n is set to
        successes + failures.
        """
        # if not np.all(np.asarray(freq_weights) == 1):
        #     self.variance = V.Binomial(n=freq_weights)
        if endog.ndim > 1 and endog.shape[1] > 1:
            y = endog[:, 0]
            # overwrite self.freq_weights for deviance below
            self.n = endog.sum(1)
            return y * 1.0 / self.n, self.n
        else:
            return endog, np.ones(endog.shape[0])

    def deviance(self, endog, mu, freq_weights=1, scale=1.0, axis=None):
        r"""
        Deviance function for either Bernoulli or Binomial data.

        Parameters
        ----------
        endog : array-like
            Endogenous response variable (already transformed to a probability
            if appropriate).
        mu : array
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            An optional scale argument. The default is 1.

        Returns
        --------
        deviance : float
            The deviance function as defined below

        """
        if np.shape(self.n) == () and self.n == 1:
            one = np.equal(endog, 1)
            return -2 * np.sum(
                (one * np.log(mu + 1e-200) + (1 - one) * np.log(1 - mu + 1e-200))
                * freq_weights,
                axis=axis,
            )

        else:
            return 2 * np.sum(
                self.n
                * freq_weights
                * (
                    endog * np.log(endog / mu + 1e-200)
                    + (1 - endog) * np.log((1 - endog) / (1 - mu) + 1e-200)
                ),
                axis=axis,
            )

    def resid_dev(self, endog, mu, scale=1.0):
        r"""
        Binomial deviance residuals

        Parameters
        -----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        scale : float, optional
            An optional argument to divide the residuals by scale. The default
            is 1.

        Returns
        -------
        resid_dev : array
            Deviance residuals as defined below

        """

        mu = self.link._clean(mu)
        if np.shape(self.n) == () and self.n == 1:
            one = np.equal(endog, 1)
            return (
                np.sign(endog - mu)
                * np.sqrt(-2 * np.log(one * mu + (1 - one) * (1 - mu)))
                / scale
            )
        else:
            return (
                np.sign(endog - mu)
                * np.sqrt(
                    2
                    * self.n
                    * (
                        endog * np.log(endog / mu + 1e-200)
                        + (1 - endog) * np.log((1 - endog) / (1 - mu) + 1e-200)
                    )
                )
                / scale
            )

    def loglike(self, endog, mu, freq_weights=1, scale=1.0):
        r"""
        The log-likelihood function in terms of the fitted mean response.

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable
        freq_weights : array-like
            1d array of frequency weights. The default is 1.
        scale : float, optional
            Not used for the Binomial GLM.

        Returns
        -------
        llf : float
            The value of the loglikelihood function evaluated at
            (endog,mu,freq_weights,scale) as defined below.

        """

        if np.shape(self.n) == () and self.n == 1:
            return scale * np.sum(
                (endog * np.log(mu / (1 - mu) + 1e-200) + np.log(1 - mu)) * freq_weights
            )
        else:
            y = endog * self.n  # convert back to successes
            return scale * np.sum(
                (
                    special.gammaln(self.n + 1)
                    - special.gammaln(y + 1)
                    - special.gammaln(self.n - y + 1)
                    + y * np.log(mu / (1 - mu))
                    + self.n * np.log(1 - mu)
                )
                * freq_weights
            )

    def resid_anscombe(self, endog, mu):
        """
        The Anscombe residuals

        Parameters
        ----------
        endog : array-like
            Endogenous response variable
        mu : array-like
            Fitted mean response variable

        Returns
        -------
        resid_anscombe : array
            The Anscombe residuals as defined below.

        References
        ----------
        Anscombe, FJ. (1953) "Contribution to the discussion of H. Hotelling's
            paper." Journal of the Royal Statistical Society B. 15, 229-30.

        Cox, DR and Snell, EJ. (1968) "A General Definition of Residuals."
            Journal of the Royal Statistical Society B. 30, 248-75.

        """
        cox_snell = lambda x: (  # noqa: E731 - skip "don't use lambda"
            special.betainc(2 / 3.0, 2 / 3.0, x) * special.beta(2 / 3.0, 2 / 3.0)
        )
        return np.sqrt(self.n) * (
            (cox_snell(endog) - cox_snell(mu))
            / (mu ** (1 / 6.0) * (1 - mu) ** (1 / 6.0))
        )
