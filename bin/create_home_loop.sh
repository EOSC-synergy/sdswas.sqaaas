#!/usr/bin/env bash

# remove images
rm -f ${HOME}/tmp/*_image??.png

wait

# create images
node  ${HOME}/js/create_home_loop.js

wait

# create animation
convert -loop 0 -delay 25 ${HOME}/tmp/*_image??.png /tmp/bdrc_animation.gif

wait

# upload to Plone

# remove again
rm -f ${HOME}/tmp/*_image??.png
