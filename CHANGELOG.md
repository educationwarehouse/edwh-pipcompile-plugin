# Changelog

<!--next-version-placeholder-->

## v0.5.3-beta.2 (2024-03-12)
### Fix
* **uv:** Improvements for 'uv' and colored diff printing, replace ansi codes with cprint ([`b8b685d`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/b8b685deed331b1eeac9d4fb9648cd997c1ea514))

## v0.5.3-beta.1 (2024-02-22)
### Performance
* Replaced 'pip-tools' with 'uv' for amazing performance ([`c58ddb0`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/c58ddb055c7230e5925a3250128f82a0ab0b346e))

## v0.5.2 (2024-02-05)
### Fix
* Split on ',' earlier and run each target in its own scope ([`24554af`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/24554af3e3c9760d577860524906420ea3ab5799))

## v0.5.1 (2024-02-05)
### Fix
* Direct tomli import instead of from isort ([`7eb7097`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/7eb709752ed5d6ce51e2bf488a084b24185e57ba))

## v0.5.0 (2024-02-05)
### Feature
* Allow setting input file(s) and output file (1) via pyproject: ([`2b67956`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/2b67956ae39c772ccc54f83d3b89d51ecad75110))

### Documentation
* Add info about usage + new pyproject config features ([`376519f`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/376519f7312920c9e2230074179a273cfaa91eb2))

## v0.4.0 (2023-12-06)
### Feature
* You can now compile/upgrade/... multiple items at the same time by comma-separating them ([`caae17c`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/caae17ce4017bcb7ca36ae312afee5d6b87b13c4))

## v0.3.0 (2023-11-03)
### Feature
* **compile:** Compile and upgrade can now also combine multiple .in files ([`2748f8c`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/2748f8cf06c0a5890a91827752c3871b12092a0e))
* Allow merging multiple .in files (for whitelabel etc) ([`de9b19d`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/de9b19d2368da47fbd36eeab01852e2d0ab5fd73))

## v0.2.2 (2023-07-07)

### Fix

* `pip-compile` executable sometimes not found ([`50677e7`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/50677e7da3e049cc823af43dd93652b0a1ec5048))

## v0.2.1 (2023-05-31)


## v0.2.0 (2023-05-08)
### Feature
* Import main tasks to __init__ so this plugin can be used as a library ([`61611cf`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/61611cf0f795221615e4e802bf8209280b1ef854))

## v0.1.9 (2023-05-04)
### Fix
* **compile:** Reverting change ([`6651cd7`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/6651cd77a07dfe9a7befee5bea39bfeff61ae061))

## v0.1.8 (2023-05-04)
### Fix
* **compile:** Allow multiple paths to be compiled at once. ([`2318a81`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/2318a81929ea2425845fb5569e018407a2a4cf52))

## v0.1.7 (2023-05-01)
### Fix
* **upgrade:** `pip.upgrade` now actually includes the upgrade flag to pip-compile ([`8ada23d`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/8ada23df192f3813a6628c0ca77169dadae058ca))

## v0.1.6 (2023-04-17)
### Fix
* **semver:** Semantic-release types should be a comma-separated string, not an array ([`4dd0394`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/4dd039434decb2ed8e2b1feff6a061f5bc49b4e3))

## v0.1.5 (2023-04-17)


## v0.1.4 (2023-04-17)
### Fix
* **project:** Remove theoretical support for Python versions below 3.10 since that has never worked ([`13f55b0`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/13f55b00cdc4f69c773c9771509e069dce2b8109))

## v0.1.3 (2023-04-11)
### Fix
* **pip.test:** Remove debug task ([`593dc8c`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/593dc8c4704dd17b519ae1bd8310938399d49b95))

## v0.1.2 (2023-04-11)
### Fix
* **deps:** Remove `pip.install-pip-tools` since that is a dependency of the plugin already ([`52a0658`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/52a0658d89e60bbc7a6ef972fc2638105090fa91))

### Documentation
* **readme:** Reference to changelog ([`0c28681`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/0c28681f36f56096cddf2cf0e7728a21b96fd42d))
* **changelog:** Manual fix changelog for missing version ([`0bce078`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/0bce078164b04ec93e26927294edf1a3daa76334))

## v0.1.1 (2023-04-11)
### Feature
* initial version of this plugin. ([`5624dd9`](https://github.com/educationwarehouse/edwh-pipcompile-plugin/commit/5624dd982dd0b1362616c2796209a1365fe966eb))
