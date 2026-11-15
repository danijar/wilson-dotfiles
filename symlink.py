import argparse
import pathlib


def is_child(child, parent):
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def remove_broken_links(repo, user):
    # Only search in one level into directories that are mirrored in the
    # repository and only report broken links that point to the repository. It's
    # good to be careful because links in mounted network drives may seem broken
    # for the client.
    for directory in repo.glob("**/*"):
        if not directory.is_dir():
            continue
        for path in (user / directory.relative_to(repo)).glob("*"):
            target = path.resolve()
            if is_child(target, repo) and not target.exists():
                print("Broken:", path)
                path.unlink()


def create_links(repo, user, overlay=None):
    for path in repo.glob("**/*"):
        if should_skip(path, repo, overlay):
            continue
        dest = user / path.relative_to(repo)
        if path.is_dir():
            dest.mkdir(exist_ok=True)
            continue
        if dest.is_symlink() and not dest.exists():
            dest.unlink()
        if not dest.exists():
            print("Create:", dest, "->", path)
            dest.symlink_to(path)
            continue
        if dest.is_symlink() and is_child(dest.resolve(), repo):
            if dest.resolve() != path:
                message = f"Expected existing {dest} to resolve to {path} "
                message += f"but resolved to {dest.resolve()} instead."
                raise RuntimeError(message)
            continue
        print("Exists:", dest)


def should_skip(path, repo, overlay):
    relative = path.relative_to(repo)
    parts = relative.parts
    return (
        path == pathlib.Path(__file__)
        or ".git" in parts
        or parts[0] == "users"
        or path.name in (".gitignore", "README.md")
        or bool(overlay) and (overlay / relative).is_file()
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default=None)
    args = parser.parse_args()
    repo = (pathlib.Path(__file__).parent).resolve()
    user = pathlib.Path("~").expanduser().resolve()
    remove_broken_links(repo, user)
    overlay = args.user and repo / "users" / args.user
    assert not overlay or overlay.is_dir(), overlay
    create_links(repo, user, overlay)
    if overlay:
        create_links(overlay, user)
    print("Done.")


if __name__ == "__main__":
    main()
