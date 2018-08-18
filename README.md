# impostormaker
Impostor construction tool for Second Life

This program starts from a set of pictures taken at different angles as a target
object is rotated in front of a green screen. The green screen is framed with a
red frame as a size reference. Impostormaker clips out the red frame, removes the
green screen background, resizes the images to eliminate extra space, combines
them into one image with the textures in a vertical row, and outputs a .png file
for use in Second Life.

Under construction

# Texture adjustment notes

After generating a texture for an impostor, it will look dim in the Second Life world.
This is because it is lit twice, one when the pictures for the impostor are taken,
and once when the impostor texture is rendered in scene. Remapping the levels for the
texture so that black renders at 50% brightness and white renders at 100% seems to help.
This needs further testing.
