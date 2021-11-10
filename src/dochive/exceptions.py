from click import ClickException, echo


class ProfileBuilderException(ClickException):
    """Base exceptions for all Profile Builder Exceptions"""


class Abort(ProfileBuilderException):
    """Abort the build"""
    def show(self, **kwargs):
        echo(self.format_message())


class ConfigurationError(ProfileBuilderException):
    """Error in configuration"""


class BuildError(ProfileBuilderException):
    """Error during the build process"""
