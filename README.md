# p-hash-benchmark

This is a project created for a thesis by the following creators.

- Henrik

- Simen

- Thias

- Martin

This program evaluates the effectiveness of perceptual hashing in detecting whether an image of a person has been previously submitted to a system.

In facial recognition systems, an attacker may attempt to gain unauthorized access by resubmitting an image that has already been used. To prevent this, the system must be able to identify duplicate images and distinguish them from images submitted by legitimate users.

The problem becomes more challenging when attackers submit slightly modified versions of an existing image to make them appear new. This program tests whether such modifications are still similar enough to be detected using perceptual hashing.

By comparing perceptual hashes of original and modified images, the program helps assess whether perceptual hashing is a viable method for identifying reused or altered images in facial recognition systems.

## How to use
Prerequisites:
- Podman
- Python 3.11+
- Linux (Tested on arch)

1. Add images to the `$HOME/.local/share/p-hash/images/` directory
2. run `rebuild.sh`
3. connect to `http://localhost:8005`
4. run `/admin/start/all`. Then after all images are hashed run `/admin/start/match`
5. Use SQL to extract data, schema found in `db/init.sql `

### Adding Methods
To add modifications/hashing_methods add them to the `modify_image/src/modification.py` or `hash_image/src/hash_image.py`. Use the `@Modifications`  or `@HashingMethods` decorators and implement the `Modification` or `HashinMethod` interface.


## Features

- Modifies images based on a set of modifications.
- Matches all hashes against others of the same types. Skips (A,B) if (B,A) already exists but not (A,A).

## To Do
- Add caching to the modification and hashing components.
