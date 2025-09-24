1. **Initialize a new Git repository:**
   git init

2. **Add a Git subtree (e.g., adding `meraki_tools` folder as a subtree):**
   git subtree add --prefix=meraki_tools <repository-url> <branch> --squash

3. **Update the subtree with latest changes from its remote repository:**
   git subtree pull --prefix=meraki_tools <repository-url> <branch> --squash

4. **Stage changes for commit:**
   git add .

5. **Commit staged changes with a message:**
   git commit -m "Your commit message here"

6. **Push commits to the main remote repository:**
   git push origin main

7. **Push changes in the subtree back to its remote repository:**
   git subtree push --prefix=meraki_tools <repository-url> <branch>

8. **Add a remote repository if not set:**
   git remote add meraki-tools <repository-url>