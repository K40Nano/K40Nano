#######################################################################
def none_function(dummy=None):
    # Don't delete this function (used in make_egv_data)
    pass


def ecoord_adj(ecoords_adj_in, scale, FlipXoffset):
    if FlipXoffset > 0:
        e0 = int(round((FlipXoffset - ecoords_adj_in[0]) * scale, 0))
    else:
        e0 = int(round(ecoords_adj_in[0] * scale, 0))
    e1 = int(round(ecoords_adj_in[1] * scale, 0))
    e2 = ecoords_adj_in[2]
    return e0, e1, e2


def make_egv_vector_data(
        controller,
        ecoords_in,
        startX=0,
        startY=0,
        units='in',
        feed=None,
        board=None,
        update_gui=None,
        stop_calc=None,
        FlipXoffset=0,
        Slow_Rapids=False):
    ########################################################
    if stop_calc is None:
        stop_calc = [0]
    if update_gui is None:
        update_gui = none_function
    ########################################################
    if units == 'in':
        scale = 1000.0
    if units == 'mm':
        scale = 1000.0 / 25.4

    startX = int(round(startX * scale, 0))
    startY = int(round(startY * scale, 0))

    ########################################################
    variable_feed_scale = None
    laser_on = True
    if feed == None:
        variable_feed_scale = 25.4 / 60.0
        feed = round(ecoords_in[0][3] * variable_feed_scale, 2)
        laser_on = False

    speed = board.make_speed(feed)

    for code in speed:
        controller.write_raw(code)

    lastx, lasty, last_loop = ecoord_adj(ecoords_in[0], scale, FlipXoffset)
    if not Slow_Rapids:
        controller.make_dir_dist(lastx - startX, lasty - startY)
    controller.flush(laser_on=False)
    controller.stream.write(b'NRB')
    # Insert "S1E"
    controller.stream.write(b'S1E')
    laser = False

    if Slow_Rapids:
        controller.rapid_move_slow(lastx - startX, lasty - startY)

    for i in range(1, len(ecoords_in)):
        e0, e1, e2 = ecoord_adj(ecoords_in[i], scale, FlipXoffset)
        update_gui("Generating EGV Data: %.1f%%" % (100.0 * float(i) / float(len(ecoords_in))))
        if stop_calc[0] == True:
            raise Exception("Action Stopped by User.")

        if (e2 == last_loop) and (not laser):
            laser = True
        elif (e2 != last_loop) and (laser):
            laser = False
        dx = e0 - lastx
        dy = e1 - lasty

        min_rapid = 5
        if (abs(dx) + abs(dy)) > 0:
            if laser:
                if variable_feed_scale is not None:
                    feed_current = round(ecoords_in[i][3] * variable_feed_scale, 2)
                    laser_on = ecoords_in[i][4] > 0
                    if feed != feed_current:
                        feed = feed_current
                        controller.flush()
                        controller.change_speed(feed, board, laser_on=laser_on)
                controller.make_cut_line(dx, dy, laser_on)
            else:
                if abs(dx) < min_rapid and abs(dy) < min_rapid:
                    controller.rapid_move_slow(dx, dy)
                else:
                    controller.rapid_move_fast(dx, dy)

        lastx = e0
        lasty = e1
        last_loop = e2

    if laser:
        laser = False

    dx = startX - lastx
    dy = startY - lasty
    if ((abs(dx) < min_rapid) and (abs(dy) < min_rapid)) or Slow_Rapids:
        controller.rapid_move_slow(dx, dy)
    else:
        controller.rapid_move_fast(dx, dy)

    # Append Footer
    controller.flush(laser_on=False)
    controller.raw_write(b'FNSE')
    return


def make_egv_raster_data(controller,
                         ecoords_in,
                         startX=0,
                         startY=0,
                         units='in',
                         feed=None,
                         board=None,
                         raster_step=0,
                         update_gui=None,
                         stop_calc=None,
                         FlipXoffset=0,
                         Slow_Rapids=False):
    ########################################################
    if stop_calc is None:
        stop_calc = [0]
    if update_gui is None:
        update_gui = none_function
    ########################################################
    if units == 'in':
        scale = 1000.0
    if units == 'mm':
        scale = 1000.0 / 25.4

    startX = int(round(startX * scale, 0))
    startY = int(round(startY * scale, 0))

    ########################################################
    variable_feed_scale = None
    laser_on = True
    if feed == None:
        variable_feed_scale = 25.4 / 60.0
        feed = round(ecoords_in[0][3] * variable_feed_scale, 2)
        laser_on = False

    speed = board.make_speed(feed, step=raster_step)

    # self.write(ord("I"))
    for code in speed:
        controller.write_raw(code)

    rapid_flag = True
    ###################################################
    scanline = []
    scanline_y = None
    if raster_step < 0.0:
        irange = range(len(ecoords_in))
    else:
        irange = range(len(ecoords_in) - 1, -1, -1)

    for i in irange:
        if i % 1000 == 0:
            update_gui("Preprocessing Raster Data: %.1f%%" % (100.0 * float(i) / float(len(ecoords_in))))
        y = ecoords_in[i][1]
        if y != scanline_y:
            scanline.append([ecoords_in[i]])
            scanline_y = y
        else:
            if bool(FlipXoffset) ^ bool(raster_step > 0.0):  # ^ is bitwise XOR
                scanline[-1].insert(0, ecoords_in[i])
            else:
                scanline[-1].append(ecoords_in[i])
    lastx, lasty, last_loop = ecoord_adj(scanline[0][0], scale, FlipXoffset)

    DXstart = lastx - startX
    DYstart = lasty - startY
    controller.make_dir_dist(DXstart, DYstart)
    # insert "NRB"
    controller.flush(laser_on=False)
    if raster_step < 0.0:
        controller.raw_write(b'NRB')
    else:
        controller.raw_write(b'NLB')
    controller.raw_write(b'S1E')
    # Insert "S1E"

    sign = -1
    cnt = 1
    for scan_raw in scanline:
        scan = []
        for point in scan_raw:
            e0, e1, e2 = ecoord_adj(point, scale, FlipXoffset)
            scan.append([e0, e1, e2])
        update_gui("Generating EGV Data: %.1f%%" % (100.0 * float(cnt) / float(len(scanline))))
        if stop_calc[0]:
            raise Exception("Action Stopped by User.")
        cnt = cnt + 1
        ######################################
        ## Flip direction and reset loop    ##
        ######################################
        sign = -sign
        last_loop = None
        y = scan[0][1]
        dy = y - lasty
        if sign == 1:
            xr = scan[0][0]
        else:
            xr = scan[-1][0]
        dxr = xr - lastx
        ######################################
        ## Make Rapid move if needed        ##
        ######################################
        if abs(dy - raster_step) != 0 and not rapid_flag:
            if dxr * sign < 0:
                yoffset = -raster_step * 3
            else:
                yoffset = -raster_step

            if (dy + yoffset) * (abs(yoffset) / yoffset) < 0:
                controller.flush(laser_on=False)
                controller.raw_write(b'N')
                controller.make_dir_dist(0, dy + yoffset)
                controller.flush(laser_on=False)
                controller.raw_write(b'SE')
                rapid_flag = True
            else:
                adj_steps = int(dy / raster_step)
                for stp in range(1, adj_steps):

                    adj_dist = 5
                    controller.make_dir_dist(sign * adj_dist, 0)
                    lastx = lastx + sign * adj_dist

                    sign = -sign
                    if sign == 1:
                        xr = scan[0][0]
                    else:
                        xr = scan[-1][0]
                    dxr = xr - lastx

            lasty = y
            ######################################
        if sign == 1:
            rng = range(0, len(scan), 1)
        else:
            rng = range(len(scan) - 1, -1, -1)
        ######################################
        ## Pad row end if needed ##
        ###########################
        pad = 2
        if dxr * sign <= 0.0:
            if rapid_flag:
                controller.make_dir_dist(dxr, 0)
            else:
                controller.make_dir_dist(-sign * pad, 0)
                controller.make_dir_dist(dxr, 0)
                controller.make_dir_dist(sign * pad, 0)
            lastx = lastx + dxr

        rapid_flag = False
        ######################################
        for j in rng:
            x = scan[j][0]
            dx = x - lastx
            ##################################
            loop = scan[j][2]
            if loop == last_loop:
                controller.make_cut_line(dx, 0, True)
            else:
                if dx * sign > 0.0:
                    controller.make_dir_dist(dx, 0)
            lastx = x
            last_loop = loop
        lasty = y

        # Make final move to ensure last move is to the right
    controller.make_dir_dist(pad, 0)
    lastx += pad
    # If sign is negative the final move will have incremented the
    # "y" position so adjust the lasty to accomodate
    if sign < 0:
        lasty += raster_step

    controller.flush(laser_on=False)

    controller.raw_write(b'N')
    dx_final = (startX - lastx)
    if raster_step < 0:
        dy_final = (startY - lasty) + raster_step
    else:
        dy_final = (startY - lasty) - raster_step
    controller.make_dir_dist(dx_final, dy_final)
    controller.flush(laser_on=False)
    controller.raw_write(b'SE')
    ###########################################################

    # Append Footer
    controller.flush(laser_on=False)
    controller.raw_write(b'FNSE')
    return
