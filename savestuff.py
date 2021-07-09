    def fill_captures(self, capture):
        captures = []
        empty = np.uint32(~(self.black | self.white))

        if self.side == self.B:
            _, white, kings = self.update_board(capture)
            piece = empty & capture
            self.print_board(piece, white, kings)
            captures.extend(self.pawnking_captures(empty, piece, (piece & kings), white))
        else:
            black, _, kings = self.update_board(capture)
            piece = empty & capture
            captures.extend(self.pawnking_captures(empty, (piece & kings), piece, black))

        return captures, piece

    def get_sequencesv2(self, capture):
        record = {}
        sequences = []

        while True:
            while True:
                fullcaps, piece = self.fill_captures(capture)

                if fullcaps:
                    fullseq = [((capture | cap) & ~piece) for cap in fullcaps]
                    record[str(capture)] = fullseq
                    capture = fullseq[0]
                else:
                    sequences.append(capture)
                    record[str(capture)] = []
                    break
            
            if record:
                while True:
                    node = np.uint32(int(capture))
                    del record[str(node)]
                    if not record:
                        return sequences
                    parent = [i for i in record.keys()][-1]
                    record[parent].remove(node)
                    if record[parent]:  
                        capture = record[parent][0]
                        break
                    else:
                        capture = parent
            else:
                return sequences
