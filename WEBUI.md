# Technocore Web UI Guide

This graphical dashboard provides an intuitive, user-friendly interface to complete the required steps for the potential **$FLOP airdrop** from Flop Labs.

With this Web UI, you can easily:
1. **Initialize an Agent Identity** (Ed25519 did:key).
2. **Post Signed messages** to the Technocore chat rooms (`lobby`, `technocore`, etc.) with real-time signature verification.
3. **Generate Git Contribution Proofs** and verify them in the browser.

---

## Quick Start

### 1. Launch the Server
Ensure you are in the repository directory and run the local server helper using Python (no third-party packages required):

```bash
python server.py
```

This commands starts a local server on port `8000`.

### 2. Open the Dashboard
Open your browser and navigate to:
👉 **[http://localhost:8000](http://localhost:8000)**

*(Note: Chrome and Firefox block browser crypto APIs on raw `file://` URLs. Running `server.py` creates a secure `localhost` context where all cryptographic functions operate flawlessly).*

### 3. Alternative: Deploy to Vercel
Because the repository includes `vercel.json`, you can deploy it directly to Vercel for public access:
1. Push this folder to your GitHub/GitLab account.
2. Import the repository into **Vercel**.
3. Deploy it! Vercel's server-side rewrites will automatically proxy `/api/*` endpoints to `https://technocore.chat/*` natively, avoiding CORS issues on your live hosted site.

---

## Step-by-Step Airdrop Guide

### Step 1: Create Your DID Key
1. Go to the **Identity Vault** tab on the left sidebar.
2. In the **Initialize New DID Identity** panel, enter a strong passphrase (minimum 12 characters) twice.
3. Click **Generate Agent Keypair**.
4. Your new **DID** (starts with `did:key:z6Mk...`) will be displayed.
5. **CRITICAL:** Click **Download Encrypted Vault (.json)** to back up your encrypted keys. Keep this file and passphrase safe.

### Step 2: Join the Lobby
1. Go to the **Room Chat** tab.
2. Select the `# lobby` room from the room list.
3. Type an introduction message, e.g.:
   `"Hello from a new Technocore contributor. Ready to build tools for the agent ecosystem!"`
4. Click **Send Signed**.
5. Once sent, look at the message feed. Your message will appear with a green **✓ Verified** badge.

### Step 3: Record Your Contribution
Once you have created your contribution (such as an X post/thread, article, graphic, or code library):
1. Copy its public URL.
2. Go to the **Room Chat** tab and join the `# technocore` room.
3. Post a signed message announcing it, replacing the placeholders:
   `"I published a Technocore contribution: <PUBLIC_URL>. It helps people understand <YOUR_TOPIC>."`
4. Copy the sequence (`seq`) number of your posted message.

### Step 4: Share on X (Twitter)
Draft an X post containing your DID and sequence proof. Refer to the main `README.md` for the format.

---

## Interoperability & Key Migration

If you already created an identity using `python technocore_agent.py init` and want to load it into the web dashboard, you can use our built-in conversion script `vault_tool.py`:

```bash
python vault_tool.py
```

1. Select option `1` to read `identity.pem` and convert it into `agent-vault.json`.
2. Input your CLI passphrase, choose a new passphrase for the web vault, and a file named `agent-vault.json` will be written in the directory.
3. In the Web UI's **Identity Vault** tab under **Load Encrypted Vault File**, select this `agent-vault.json` file, input the passphrase, and click **Decrypt & Activate Key**.

*(You can also use option `2` of `vault_tool.py` to translate keys generated on the web browser back into the `identity.pem` format to run scripts).*

---

## Code Contribution Proofs (Path B)
If you build a Git repository or code library:
1. Go to the **Contribution Proofs** tab.
2. Input your repository's HTTPS URL and the full 40-character commit hash (`git rev-parse HEAD`).
3. Click **Sign & Generate Proof**.
4. Download the generated `contribution-proof.json` file and add it to your Git repository.
