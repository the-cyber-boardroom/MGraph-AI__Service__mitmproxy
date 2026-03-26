"""CLI entry point — mitm-scripts command."""

import argparse
import os
import sys
from pathlib import Path

from mitm_scripts.config       import load_env, validate_config
from mitm_scripts.cache_client import setup_client, resolve_cache_id

SITES_DIR   = 'sites'
SAMPLES_DIR = 'samples'
DATA_KEY_PREFIX = 'sites'
DATA_FILE_ID    = 'data'


def get_project_dir():
    """Find project dir — walk up from cwd looking for .env."""
    d = Path.cwd()
    while d != d.parent:
        if (d / '.env').exists():
            return str(d)
        d = d.parent
    return str(Path.cwd())


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path


def data_key_for_domain(domain):
    return f"{DATA_KEY_PREFIX}/{domain}/filter.js"


# ═══════════════════════════════════════════════════════════════════════════
# Commands
# ═══════════════════════════════════════════════════════════════════════════

def cmd_status(args, config, client, cache_id, namespace):
    """Check connection and show config."""
    print(f"  ✓ Connected to: {config['CACHE_SERVICE_BASE_URL']}")
    print(f"  ✓ Namespace:    {namespace}")
    print(f"  ✓ Cache ID:     {cache_id}")

    health = client.health()
    print(f"  ✓ Health:       {'OK' if health else 'FAILED'}")


def cmd_list(args, config, client, cache_id, namespace):
    """List all domains with scripts in S3."""
    result = client.data().list().data__list__with__key(
        cache_id  = cache_id,
        namespace = namespace,
        data_key  = DATA_KEY_PREFIX,
        recursive = True)

    if not result or not result.files:
        print("  No inject scripts found in S3")
        return

    domains = {}
    for f in result.files:
        # data_key is: sites/{domain}/filter.js
        parts = f.data_key.split('/')
        if len(parts) >= 2:
            domain = parts[1]
            domains[domain] = f.file_size

    if domains:
        print(f"  Inject scripts ({len(domains)} domains):\n")
        for d in sorted(domains):
            size = domains[d]
            stub = size < 100
            marker = '○' if stub else '✓'
            print(f"    {marker} {d:<30} {size:>6} bytes{'  (stub)' if stub else ''}")
    else:
        print("  No domains found")


def cmd_pull(args, config, client, cache_id, namespace):
    """Pull scripts from S3 to local sites/ directory."""
    project_dir = get_project_dir()
    sites_dir   = ensure_dir(os.path.join(project_dir, SITES_DIR))
    domain      = getattr(args, 'domain', None)

    if domain:
        domains = [domain]
    else:
        # List all domains first
        result = client.data().list().data__list__with__key(
            cache_id=cache_id, namespace=namespace,
            data_key=DATA_KEY_PREFIX, recursive=True)

        if not result or not result.files:
            print("  No scripts found in S3")
            return

        domains = set()
        for f in result.files:
            # data_key is: sites/{domain}/filter.js
            parts = f.data_key.split('/')
            if len(parts) >= 2:
                domains.add(parts[1])
        domains = sorted(domains)

    if not domains:
        print("  No domains found")
        return

    print(f"  Pulling {len(domains)} domain(s)...\n")

    for d in domains:
        data_key = data_key_for_domain(d)
        try:
            content = client.data().retrieve().data__string__with__id_and_key(
                cache_id=cache_id, namespace=namespace,
                data_key=data_key, data_file_id=DATA_FILE_ID)

            if content:
                domain_dir = ensure_dir(os.path.join(sites_dir, d))
                out_path = os.path.join(domain_dir, 'filter.js')
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"    ✓ {d}/filter.js  ({len(content):,} chars)")
            else:
                print(f"    ○ {d}/filter.js  (empty or not found)")

        except Exception as e:
            print(f"    ✗ {d}/filter.js  ERROR: {e}")

    print(f"\n  Saved to: {sites_dir}/")


def cmd_push(args, config, client, cache_id, namespace):
    """Push local scripts to S3."""
    project_dir = get_project_dir()
    sites_dir   = os.path.join(project_dir, SITES_DIR)
    domain      = getattr(args, 'domain', None)
    sample      = getattr(args, 'sample', None)

    if sample:
        # Push a sample script to a specific domain
        if not domain:
            print("  Error: --sample requires a domain. Usage: push <domain> --sample <name>")
            sys.exit(1)

        sample_path = os.path.join(project_dir, SAMPLES_DIR, sample)
        if not sample_path.endswith('.js'):
            sample_path += '.js'

        if not os.path.isfile(sample_path):
            print(f"  Error: sample not found: {sample_path}")
            print(f"  Available samples:")
            samples_dir = os.path.join(project_dir, SAMPLES_DIR)
            if os.path.isdir(samples_dir):
                for f in sorted(os.listdir(samples_dir)):
                    if f.endswith('.js'):
                        print(f"    {f}")
            sys.exit(1)

        with open(sample_path, 'r', encoding='utf-8') as f:
            content = f.read()

        _push_script(client, cache_id, namespace, domain, content, f"sample:{os.path.basename(sample_path)}")
        return

    if domain:
        # Push a single domain
        script_path = os.path.join(sites_dir, domain, 'filter.js')
        if not os.path.isfile(script_path):
            print(f"  Error: {script_path} not found")
            print(f"  Run 'mitm-scripts pull' first, or create the file manually")
            sys.exit(1)

        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        _push_script(client, cache_id, namespace, domain, content, f"sites/{domain}/filter.js")
        return

    # Push all
    if not os.path.isdir(sites_dir):
        print(f"  Error: {sites_dir}/ not found. Run 'mitm-scripts pull' first.")
        sys.exit(1)

    domains = [d for d in sorted(os.listdir(sites_dir))
               if os.path.isfile(os.path.join(sites_dir, d, 'filter.js'))]

    if not domains:
        print(f"  No scripts found in {sites_dir}/")
        return

    print(f"  Pushing {len(domains)} domain(s)...\n")

    for d in domains:
        script_path = os.path.join(sites_dir, d, 'filter.js')
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        _push_script(client, cache_id, namespace, d, content, f"sites/{d}/filter.js")

    print()


def _push_script(client, cache_id, namespace, domain, content, source_label):
    """Push a script to S3 for a domain."""
    data_key = data_key_for_domain(domain)

    try:
        result = client.data_store().data__store_string__with__id_and_key(
            cache_id     = cache_id,
            namespace    = namespace,
            data_key     = data_key,
            data_file_id = DATA_FILE_ID,
            body         = content)

        if result:
            print(f"    ✓ {domain}  ← {source_label} ({len(content):,} chars)")
        else:
            print(f"    ✗ {domain}  FAILED (no response)")

    except Exception as e:
        print(f"    ✗ {domain}  ERROR: {e}")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        prog='mitm-scripts',
        description='Manage inject scripts in S3 for the MITM proxy')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # status
    subparsers.add_parser('status', help='Check connection and show config')

    # list
    subparsers.add_parser('list', help='List all domains with scripts in S3')

    # pull
    p_pull = subparsers.add_parser('pull', help='Pull scripts from S3 to local sites/ directory')
    p_pull.add_argument('domain', nargs='?', help='Pull a single domain (optional)')

    # push
    p_push = subparsers.add_parser('push', help='Push local scripts to S3')
    p_push.add_argument('domain', nargs='?', help='Push a single domain (optional, default: all)')
    p_push.add_argument('--sample', '-s', help='Push a sample script (from samples/) to the domain')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # ── Load config ────────────────────────────────────────────
    project_dir = get_project_dir()
    config = load_env(project_dir)
    missing = validate_config(config)

    if missing:
        print(f"\n  ✗ Missing config in .env: {', '.join(missing)}\n")
        print(f"  Create a .env file with:\n")
        print(f'    CACHE_SERVICE_BASE_URL=https://your-cache-service.example.com')
        print(f'    CACHE_SERVICE_API_KEY=your-api-key')
        print(f'    CACHE_NAMESPACE=your-namespace')
        print()
        sys.exit(1)

    namespace = config['CACHE_NAMESPACE']

    # ── Connect ────────────────────────────────────────────────
    try:
        client   = setup_client(config)
        cache_id = resolve_cache_id(client, namespace, config.get('INJECT_CACHE_KEY', 'inject'))
    except Exception as e:
        print(f"\n  ✗ Connection failed: {e}\n")
        print(f"  Check .env settings:")
        print(f"    CACHE_SERVICE_BASE_URL = {config.get('CACHE_SERVICE_BASE_URL', '(not set)')}")
        print(f"    CACHE_SERVICE_API_KEY  = {'***' if config.get('CACHE_SERVICE_API_KEY') else '(not set)'}")
        print(f"    CACHE_NAMESPACE        = {config.get('CACHE_NAMESPACE', '(not set)')}")
        print()
        sys.exit(1)

    print()

    # ── Dispatch ───────────────────────────────────────────────
    commands = {
        'status': cmd_status,
        'list'  : cmd_list,
        'pull'  : cmd_pull,
        'push'  : cmd_push,
    }

    commands[args.command](args, config, client, cache_id, namespace)
    print()


if __name__ == '__main__':
    main()