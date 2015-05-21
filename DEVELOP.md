Tucker Sync Development
=======================

These workflows are for contributing to the development of Tucker Sync itself.  
For the setup of an application server see INSTALL.md.

**Developers without Commit Access**

Please fork and send a rebased merge/pull request.

**Developers with Commit Access**

Please follow the rebase workflow below.

Git Rebase Workflow
===================

Rebase workflow is simply taking a block of commits and replaying them on top of existing commits.  

 - Avoid spaghetti merge. 
 - Solve conflicts sooner.
 - Banish `git pull' from thy vocabulary!
 
Basic: work directly on master or local branches for small commits.  
Advanced: remote tracking, environment and feature branches.

Master
------

If you have commits on master:

    git fetch                           # Fetch from the current branch remote: origin/master.
    git rebase                          # Rebase local commits onto (on top of): origin/master.
    git push                            # Push to remote: master = origin/master.

Local Branch
------------

Branch and develop on a local branch (feature or fix):

    git checkout -b local               # create branch 'local'.

 - Can be done with working copy changes.
 - Can always rename the branch later:
    - git branch -m local-feature
    - git branch -m local-fix

Commit early and often:

    git add file
    git commit -m "Fix: fixed it."
    git add file
    git commit -m "Improve: refactored it."

Rebase often onto upstream:

    git fetch origin master
    git rebase master

Interactive rebase (optional):

    git rebase -i master

Fast-forward master:

    git checkout master
    git rebase local                    # this will fast-forward.
    git push

Remember
--------

Don't `git pull` (remember that git pull is fetch && merge).

Don't force-push to a remote.

Don't amend commits that have been pushed.

Don't make permalinks to non permanent branches.  
Feature and fix branches aren't permanent.  
Feature and fix branches are 'to the left' of master.  
Permanent branches are 'to the right' of master.

Clean working copy state is less to think about when performing operations.  
Use git stash and unstash.  
Untracked files are usually not a problem here.

Remote Tracking Branch
----------------------

To share a feature branch the rebase workflow above is applied.  
Only apply the workflow to a remote tracking feature branch instead of master.

Create the branch:

    git checkout master
    git checkout -b feature
    git push -u origin feature          # push feature to origin and set upstream tracking refs.

Work locally:

    git add file
    git commit -m "Improve: implement more awesomeness."

Rebase often onto upstream:

    git fetch                           # Fetch from the current branch remote: origin/feature.
    git rebase                          # Rebase local commits onto (on top of): origin/feature.
    git push                            # Push to remote: feature = origin/feature.

This workflow will share and backup the feature branch.  
Note that we never have to force push.  
So sharing and collaborating on feature is safe.  
The feature branch will diverge from master.  
(Hint: to bring development up to date with master: branch, rebase and push a new branch in a similar way)

Integrate with master:

    git checkout feature                # feature is ready to integrate with master.
    git checkout -b temp                # temporary branch off of feature.

    git rebase master                   # rebase temp onto master.

    git checkout master
    git rebase temp                     # this will fast-forward.
    git push

    git branch -d temp                  # delete temp branch.

    git push origin --delete feature    # optional cleanup.

Note that with this approach the exact feature branch commits will be deleted when feature branch is deleted.  
Therefore these revision numbers can't be used as permalinks.  
A commit revision number (hash) isn't permanent until it's applied on top of a permanent branch like master.

Delete Branch
-------------

Prune remote tracking branches that have been deleted:

    git fetch --prune

http://stackoverflow.com/questions/2003505/delete-a-git-branch-both-locally-and-remotely

Gems
----

git pull --rebase        # fetch remote and rebase local commits instead of merging.
git fetch --all          # fetch all remote tracking branches.
git rebase --continue    # continue a rebase after fixing conflicts.

git log -n 10 --graph --abbrev-commit --decorate --date=relative --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)' --all

git config --global alias.lg "log --graph --abbrev-commit --decorate --date=relative --format=format:'%C(bold blue)%h%C(reset) - %C(bold green)(%ar)%C(reset) %C(white)%s%C(reset) %C(dim white)- %an%C(reset)%C(bold yellow)%d%C(reset)' --all"

git lg -n10

Release
-------

A continuously deployable master is not a goal of this project.  
Release candidates (rc) should be selected, tagged, and tested.  
Release branches are only needed if commits after the release tag are required.  
Release and environment branches are 'to the right' of master.  
Possibly use a production environment branch as per GitLab flow:  
https://gitlab.com/help/workflow/gitlab_flow.md  
