datetime.txt is read by the last job (simulate-deployments-from-selected-repos)
in the stochastic-committer repo's main.yml workflow.

Its content must be exactly one line in this format:

    <repo-name> <unix-epoch-timestamp>

Example:

    price-index 1776316931
